# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""
Multi Repository Management.

The :any:`GitWS` class provides a simple facade to all inner `GitWS` functionality.
"""
import logging
import shutil
import urllib
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from ._util import no_echo, removesuffix, resolve_relative, run
from .clone import Clone, map_paths
from .const import MANIFEST_PATH_DEFAULT
from .datamodel import Manifest, ManifestSpec, Project, ProjectSpec
from .deptree import Node, get_deptree
from .exceptions import GitCloneMissingError, GitCloneNotCleanError, InitializedError, ManifestExistError
from .filters import Filter, default_filter
from .git import Git, Status
from .iters import ManifestIter, ProjectIter
from .types import Groups, ProjectFilter
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")
_COLOR_BANNER = "green"
_COLOR_ACTION = "magenta"
_COLOR_SKIP = "blue"


class GitWS:
    """
    Multi Repository Management.

    Args:
        workspace (Workspace): workspace.
        manifest_spec (ManifestSpec): manifest.
    """

    # pylint: disable=too-many-public-methods

    def __init__(self, workspace: Workspace, manifest_spec: ManifestSpec, echo=None):
        self.workspace = workspace
        self.manifest_spec = manifest_spec
        self.echo = echo or no_echo

    def __eq__(self, other):
        if isinstance(other, GitWS):
            return (self.workspace, self.manifest_spec) == (other.workspace, other.manifest_spec)
        return NotImplemented

    @property
    def path(self) -> Path:
        """
        GitWS Workspace Root Directory.
        """
        return self.workspace.path

    @staticmethod
    def from_path(path: Optional[Path] = None, manifest_path: Optional[Path] = None, echo=None) -> "GitWS":
        """
        Create :any:`GitWS` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        return GitWS(workspace, manifest_spec, echo=echo)

    @staticmethod
    def create(path: Path, main_path: Path, manifest_path: Path, groups: Groups = None, echo=None) -> "GitWS":
        """
        Create :any:`GitWS` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
            main_path:  Main Project Path.
            mainfest_path:  ManifestSpec File Path.
        """
        _LOGGER.debug("GitWS.create(%r, %r, %r, groups=%r)", str(path), str(main_path), str(manifest_path), groups)
        # We need to resolve in inverted order, otherwise the manifest_path is broken
        manifest_path = resolve_relative(manifest_path, base=main_path)
        main_path = resolve_relative(main_path, base=path)
        manifest_spec = ManifestSpec.load(path / main_path / manifest_path)
        workspace = Workspace.init(path, main_path, manifest_path, groups=groups)
        return GitWS(workspace, manifest_spec, echo=echo)

    @staticmethod
    def init(
        main_path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
        groups: Groups = None,
        force: bool = False,
        echo=None,
    ) -> "GitWS":
        """
        Initialize Workspace for git clone at `main_path`.

        :param main_path: Path within git clone. (Default is the current working directory).
        :param manifest_path: Path to the manifest file.
        """
        echo = echo or no_echo
        main_path = Git.find_path(path=main_path)
        path = main_path.parent
        info = Workspace.is_init(path)
        if info:
            raise InitializedError(path, info.main_path)
        if not force:
            Workspace.check_empty(path, main_path)
        name = main_path.name
        echo(f"===== {name} (MAIN) =====", fg=_COLOR_BANNER)
        return GitWS.create(path, main_path, manifest_path, groups, echo=echo)

    def deinit(self):
        """De-Initialize :any:`GitWS`."""
        return self.workspace.deinit()

    @staticmethod
    def clone(
        url: str,
        main_path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
        groups: Groups = None,
        force: bool = False,
        echo=None,
    ) -> "GitWS":
        """Clone git `url` and initialize Workspace."""
        echo = echo or no_echo
        parsedurl = urllib.parse.urlparse(url)
        name = Path(parsedurl.path).name
        if main_path is None:
            main_path = Path.cwd() / removesuffix(name, ".git")
        main_path_rel: Path = resolve_relative(main_path)
        path = main_path_rel.parent
        if not force:
            Workspace.check_empty(path, main_path_rel)
        echo(f"===== {main_path_rel.name} (MAIN) =====", fg=_COLOR_BANNER)
        echo(f"Cloning {url!r}.", fg=_COLOR_ACTION)
        git = Git(main_path_rel)
        git.clone(url)
        return GitWS.create(path, main_path_rel, manifest_path, groups, echo=echo)

    def update(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        skip_main: bool = False,
        prune: bool = False,
        rebase: bool = False,
        force: bool = False,
    ):
        """Create/Update all dependent projects."""
        workspace = self.workspace
        used: List[Path] = [workspace.info.main_path]
        for clone in self._foreach(
            project_paths=project_paths,
            manifest_path=manifest_path,
            groups=groups,
            skip_main=skip_main,
            resolve_url=True,
        ):
            used.append(Path(clone.project.path))
            self._check_clone(clone, revdiff=False)
            self._update(clone, rebase)
        if prune:
            self._prune(workspace, used, force=force)

    def _update(self, clone: Clone, rebase: bool):
        # Clone
        project = clone.project
        git = clone.git
        if not git.is_cloned():
            self.echo(f"Cloning {project.url!r}.", fg=_COLOR_ACTION)
            git.clone(project.url, revision=project.revision)
            return

        # Determine actual version
        tag = git.get_tag()
        branch = git.get_branch()
        sha = git.get_sha()

        if project.revision in (sha, tag) and not branch:
            self.echo("Nothing to do.", fg=_COLOR_ACTION)
            return

        revision = tag or branch or sha

        # Checkout
        fetched = False
        if project.revision and revision != project.revision:
            self.echo("Fetching.", fg=_COLOR_ACTION)
            git.fetch()
            fetched = True
            self.echo(f"Checking out {project.revision!r} (previously {revision!r}).", fg=_COLOR_ACTION)
            git.checkout(project.revision)
            branch = git.get_branch()
            revision = tag or branch or sha

        # Pull or Rebase in case we are on a branch (or have switched to it.)
        if branch:
            if rebase:
                if not fetched:
                    self.echo("Fetching.", fg=_COLOR_ACTION)
                    git.fetch()
                self.echo(f"Rebasing branch {branch!r}.", fg=_COLOR_ACTION)
                git.rebase()
            else:
                if not fetched:
                    self.echo(f"Pulling branch {branch!r}.", fg=_COLOR_ACTION)
                    git.pull()
                else:
                    self.echo(f"Merging branch {branch!r}.", fg=_COLOR_ACTION)
                    git.merge()

    def _prune(self, workspace: Workspace, used: List[Path], force: bool = False):
        for obsolete_path in workspace.iter_obsoletes(used):
            name = resolve_relative(obsolete_path, workspace.path)
            rel_path = resolve_relative(obsolete_path)
            self.echo(f"===== {name} (OBSOLETE) =====", fg=_COLOR_BANNER)
            self.echo(f"Removing {str(rel_path)!r}.", fg=_COLOR_ACTION)
            git = Git(obsolete_path)
            if force or not git.is_cloned() or git.is_clean():
                shutil.rmtree(obsolete_path, ignore_errors=True)
            else:
                raise GitCloneNotCleanError(resolve_relative(rel_path))

    def status(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        branch: bool = False,
    ) -> Generator[Status, None, None]:
        """Iterate over Status."""
        for clone in self._foreach(project_paths=project_paths, manifest_path=manifest_path, groups=groups):
            path = clone.git.path
            self._check_clone(clone)
            for status in clone.git.status(branch=branch):
                yield status.with_path(path)

    def checkout(self, paths: Tuple[Path, ...], force: bool = False):
        """Checkout."""
        if paths:
            # Checkout specific files only
            for clone, cpaths in map_paths(tuple(self.clones()), paths):
                self._echo_project_banner(clone.project)
                if cpaths:
                    clone.git.checkout(revision=clone.project.revision, paths=cpaths, force=force)
        else:
            # Checkout all branches
            for clone in self.clones(resolve_url=True):
                git = clone.git
                project = clone.project
                self._echo_project_banner(project)
                if not git.is_cloned():
                    self.echo(f"Cloning {project.url!r}.", fg=_COLOR_ACTION)
                    git.clone(project.url, revision=project.revision)
                if project.revision:
                    git.checkout(revision=project.revision, force=force)
                self._check_clone(clone)

    def add(self, paths: Tuple[Path, ...]):
        """Add."""
        if not paths:
            raise ValueError("Nothing specified, nothing added.")
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            if cpaths:
                clone.git.add(cpaths)

    # pylint: disable=invalid-name
    def rm(self, paths: Tuple[Path, ...], cached: bool = False, force: bool = False, recursive: bool = False):
        """rm."""
        if not paths:
            raise ValueError("Nothing specified, nothing removed.")
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            if cpaths:
                clone.git.rm(cpaths, cached=cached, force=force, recursive=recursive)

    def reset(self, paths: Tuple[Path, ...]):
        """Reset."""
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            if cpaths:
                clone.git.reset(cpaths)

    def commit(self, msg: str, paths: Tuple[Path, ...], all_: bool = False):
        """Commit."""
        if paths:
            # clone file specific commit
            for clone, cpaths in map_paths(tuple(self.clones()), paths):
                if cpaths:
                    self._echo_project_banner(clone.project)
                    clone.git.commit(msg, paths=cpaths, all_=all_)
        else:
            # commit changed clones
            if all_:
                clones = [clone for clone in self.clones() if clone.git.has_changes()]
            else:
                clones = [clone for clone in self.clones() if clone.git.has_index_changes()]
            for clone in clones:
                self._echo_project_banner(clone.project)
                clone.git.commit(msg, all_=all_)

    def run_foreach(
        self, command, project_paths=None, manifest_path: Path = None, groups: Groups = None, reverse: bool = False
    ):
        """Run `command` on each project."""
        for clone in self.foreach(
            project_paths=project_paths, manifest_path=manifest_path, groups=groups, reverse=reverse
        ):
            if not clone.git.is_cloned():
                raise GitCloneMissingError(clone.git.path)
            run(command, cwd=clone.git.path)

    def foreach(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        resolve_url: bool = False,
        reverse: bool = False,
    ) -> Generator[Clone, None, None]:
        """User Level Clone Iteration."""
        for clone in self._foreach(
            project_paths=project_paths,
            manifest_path=manifest_path,
            groups=groups,
            resolve_url=resolve_url,
            reverse=reverse,
        ):
            self._check_clone(clone)
            yield clone

    def _foreach(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        skip_main: bool = False,
        resolve_url: bool = False,
        reverse: bool = False,
    ) -> Generator[Clone, None, None]:
        """User Level Clone Iteration."""
        project_paths_filter = self._create_project_paths_filter(project_paths)
        groups = self.workspace.get_groups(groups=groups)
        filter_ = self.create_groups_filter(groups=groups)
        clones = self.clones(manifest_path, filter_, skip_main=skip_main, resolve_url=resolve_url, reverse=reverse)
        if groups:
            self.echo(f"Groups: {groups!r}", bold=True)
        for clone in clones:
            project = clone.project
            if project_paths_filter(project):
                self._echo_project_banner(project)
                yield clone
            else:
                self.echo(f"===== SKIPPING {project.info} =====", fg=_COLOR_SKIP)

    @staticmethod
    def _check_clone(clone, revdiff=True):
        project = clone.project
        projectrev = project.revision
        if projectrev:
            if revdiff:
                try:
                    clonerev = clone.git.get_revision()
                except FileNotFoundError:
                    clonerev = None
                if clonerev and projectrev != clonerev:
                    _LOGGER.warning("Clone %s is on different revision: %r", project.info, clonerev)
        elif not project.is_main:
            _LOGGER.warning("Clone %s has no revision!", project.info)

    def clones(
        self,
        manifest_path: Path = None,
        filter_: ProjectFilter = None,
        skip_main: bool = False,
        resolve_url: bool = False,
        reverse: bool = False,
    ) -> Generator[Clone, None, None]:
        """Iterate over Clones."""
        workspace = self.workspace
        projects = self.projects(manifest_path, filter_, skip_main=skip_main, resolve_url=resolve_url)
        if reverse:
            projects = reversed(tuple(projects))  # type: ignore
        for project in projects:
            clone = Clone.from_project(workspace, project)
            yield clone

    def projects(
        self,
        manifest_path: Optional[Path] = None,
        filter_: ProjectFilter = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ) -> Generator[Project, None, None]:
        """Iterate over Projects."""
        workspace = self.workspace
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        filter_ = filter_ or self.create_groups_filter()
        yield from ProjectIter(workspace, manifest_path, filter_=filter_, skip_main=skip_main, resolve_url=resolve_url)

    def manifests(
        self, manifest_path: Optional[Path] = None, filter_: ProjectFilter = None
    ) -> Generator[Manifest, None, None]:
        """Iterate over Manifests."""
        workspace = self.workspace
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        filter_ = filter_ or self.create_groups_filter()
        yield from ManifestIter(workspace, manifest_path, filter_=filter_)

    @staticmethod
    def create_manifest(manifest_path: Path = MANIFEST_PATH_DEFAULT) -> Path:
        """Create ManifestSpec File at `manifest_path`within `project`."""
        if manifest_path.exists():
            raise ManifestExistError(manifest_path)
        manifest_spec = ManifestSpec()
        manifest_spec.save(manifest_path)
        return manifest_path

    def get_manifest_spec(self, groups: Groups = None, freeze: bool = False, resolve: bool = False) -> ManifestSpec:
        """Get Manifest."""
        workspace = self.workspace
        manifest_spec = self.manifest_spec
        if resolve:
            rdeps: List[ProjectSpec] = []
            groups = self.workspace.get_groups(groups)
            filter_ = self.create_groups_filter(groups)
            for project in self.projects(filter_=filter_, skip_main=True):
                project_spec = ProjectSpec.from_project(project)
                rdeps.append(project_spec)
            manifest_spec = manifest_spec.update(dependencies=rdeps)
        else:
            manifest_spec = manifest_spec.copy()
        if freeze:
            manifest = Manifest.from_spec(manifest_spec)
            fdeps: List[ProjectSpec] = []
            for project_spec, project in zip(manifest_spec.dependencies, manifest.dependencies):
                project_path = workspace.get_project_path(project)
                git = Git(project_path)
                if not git.is_cloned():
                    raise GitCloneMissingError(resolve_relative(project_path))
                revision = git.get_tag() or git.get_sha()
                fdeps.append(project_spec.update(revision=revision))
            manifest_spec = manifest_spec.update(dependencies=fdeps)
        return manifest_spec

    def get_manifest(self, freeze: bool = False, resolve: bool = False) -> Manifest:
        """Get Manifest."""
        manifest_path = self.workspace.get_manifest_path()
        manifest_spec = self.get_manifest_spec(freeze=freeze, resolve=resolve)
        return Manifest.from_spec(manifest_spec, path=str(manifest_path))

    def get_deptree(self) -> Node:
        """Get Dependency Tree."""
        manifest = self.get_manifest()
        return get_deptree(self.workspace, manifest)

    def _create_project_paths_filter(self, project_paths):
        workspace_path = self.workspace.path
        if project_paths:
            project_paths = [resolve_relative(path, base=workspace_path) for path in project_paths]
            return lambda project: resolve_relative(project.path, base=workspace_path) in project_paths
        return default_filter

    def create_groups_filter(self, groups=None):
        """Create Filter Method for `groups`."""
        if groups is None:
            groups = self.workspace.get_groups()

        filter_ = Filter.from_str(groups or "")

        def func(project):
            groups = [group.name for group in project.groups]
            disabled = [group.name for group in project.groups if group.optional]
            return filter_(groups, disabled=disabled)

        return func

    def _echo_project_banner(self, project):
        self.echo(f"===== {project.info} =====", fg=_COLOR_BANNER)
