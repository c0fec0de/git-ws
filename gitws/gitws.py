# Copyright 2022-2023 c0fec0de
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

The :any:`GitWS` class provides a simple facade to all Git Workspace functionality.
"""
import logging
import shutil
import urllib
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from ._filerefupdater import CopyFileUpdater, LinkFileUpdater
from ._util import get_repr, no_echo, removesuffix, resolve_relative, run
from .appconfig import AppConfig
from .clone import Clone, map_paths
from .const import MANIFEST_PATH_DEFAULT, MANIFESTS_PATH
from .datamodel import GroupFilters, Manifest, ManifestSpec, Project, ProjectPaths, ProjectSpec
from .deptree import DepNode, get_deptree
from .exceptions import (
    GitCloneNotCleanError,
    GitTagExistsError,
    InitializedError,
    ManifestExistError,
    NoGitError,
    NoMainError,
)
from .git import DiffStat, Git, Status
from .iters import ManifestIter, ProjectIter
from .manifestfinder import find_manifest
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")
_COLOR_BANNER = "green"
_COLOR_ACTION = "magenta"
_COLOR_SKIP = "blue"


class GitWS:
    """
    Multi Repository Management.

    Args:
        workspace: The Workspace Representation.
        manifest_path: Manifest File Path. **Resolved** Path.
        group_filters: Group Filters.

    Keyword Args:
        secho: :any:`click.secho` like print method for verbose output.

    There are static methods to create a :any:`GitWS` instances in the different szenarios:

    * :any:`GitWS.from_path()`: Create :any:`GitWS` for EXISTING workspace at ``path``.
    * :any:`GitWS.create()`: Create NEW workspace at ``path`` and return corresponding :any:`GitWS`.
    * :any:`GitWS.init()`: Initialize NEW Workspace and return corresponding :any:`GitWS`.
    * :any:`GitWS.clone()`: Clone git ``url``, initialize NEW Workspace and return corresponding :any:`GitWS`.
    """

    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        workspace: Workspace,
        manifest_path: Path,
        group_filters: GroupFilters,
        secho=None,
    ):
        self.workspace = workspace
        self.manifest_path = manifest_path
        self.group_filters = group_filters
        self.secho = secho or no_echo

    def __eq__(self, other):
        if isinstance(other, GitWS):
            return (self.workspace, self.manifest_path, self.group_filters) == (
                other.workspace,
                other.manifest_path,
                other.group_filters,
            )
        return NotImplemented

    def __repr__(self):
        return get_repr(self, (self.workspace, self.manifest_path, self.group_filters))

    @property
    def path(self) -> Path:
        """
        GitWS Workspace Root Directory.
        """
        return self.workspace.path

    @property
    def main_path(self) -> Optional[Path]:
        """
        GitWS Workspace Main Directory.
        """
        return self.workspace.main_path

    @property
    def base_path(self) -> Path:
        """
        GitWS Workspace Main Directory (if the workspace has a main project) or GitWS Workspace Directory.
        """
        return self.workspace.base_path

    @staticmethod
    def from_path(
        path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        secho=None,
    ) -> "GitWS":
        """
        Create :any:`GitWS` for EXISTING workspace at ``path``.

        Keyword Args:
            path: Path within the workspace (Default is the current working directory).
            manifest_path: Manifest File Path. Relative to ``base_path``. Default is taken from Configuration.
            group_filters: Group Filters. Default is taken from Configuration.
            secho: :any:`click.secho` like print method for verbose output.
        """
        workspace = Workspace.from_path(path=path)
        main_path = workspace.main_path
        if main_path and not manifest_path:
            manifest_path = find_manifest(main_path)
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        GitWS.check_manifest(manifest_path)
        if group_filters:
            GroupFilters.validate(group_filters)
        group_filters = workspace.get_group_filters(group_filters=group_filters or None)
        return GitWS(workspace, manifest_path, group_filters, secho=secho)

    @staticmethod
    def create(
        path: Path,
        main_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        force: bool = False,
        secho=None,
    ) -> "GitWS":
        """
        Create NEW workspace at ``path`` and return corresponding :any:`GitWS`.

        Args:
            path: Workspace Path.

        Keyword Args:
            main_path: Main Project Path.
            manifest_path: Manifest File Path. Relative to ``main_path`` if given, otherwise relative to ``path``.
                           Default is ``git-ws.toml``.
                           This value is written to the configuration.
            group_filters: Default Group Filters.
                           This value is written to the configuration.
            force: Ignore that the workspace exists.
            secho: :any:`click.secho` like print method for verbose output.
        """
        _LOGGER.debug(
            "GitWS.create(%r, main_path=%r, manifest_path=%r, group-filters=%r)",
            str(path),
            str(main_path),
            str(manifest_path),
            group_filters,
        )
        # Relative to main_path if given, or workspace path as fallback
        # We need to resolve in inverted order, otherwise the manifest_path is broken
        # ``manifest_path`` can be absolute or relative to ``base_path``. we need it relative to ``base_path``.
        manifest_path_rel = resolve_relative(manifest_path or MANIFEST_PATH_DEFAULT, base=(main_path or path))
        if main_path:
            # ``main_path`` can be absolute or relative to ``path``. we need it relative to ``path``.
            main_path = resolve_relative(main_path, base=path)
            base_path = path / main_path
        else:
            base_path = path
        # check manifest
        GitWS.check_manifest(base_path / manifest_path_rel)
        # check group_filters
        if group_filters:
            GroupFilters.validate(group_filters)
        # Create Workspace
        workspace = Workspace.init(
            path,
            main_path=main_path,
            manifest_path=manifest_path_rel,
            group_filters=group_filters or None,
            force=force,
        )
        group_filters = workspace.get_group_filters(group_filters=group_filters)
        # Check for tagged manifest
        if main_path and not manifest_path:
            manifest_path_rel = find_manifest(base_path) or manifest_path_rel
        return GitWS(workspace, base_path / manifest_path_rel, group_filters, secho=secho)

    @staticmethod
    def init(
        path: Optional[Path] = None,
        main_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        force: bool = False,
        secho=None,
    ) -> "GitWS":
        """
        Initialize NEW Workspace and return corresponding :any:`GitWS`.

        Keyword Args:
            path: Workspace Path. Parent directory of the main git clone directory or current working
                  directory by default.
            main_path: Main Project Path.
            manifest_path: Manifest File Path. Relative to ``main_path``. Default is ``git-ws.toml``.
                           This value is written to the configuration.
            group_filters: Default Group Filters.
                           This value is written to the configuration.
            force: Ignore that the workspace exists.
            secho: :any:`click.secho` like print method for verbose output.

        This method has different modes depending on ``main_path`` and the current working directory:

        * if ``main_path`` refers to a git clone, it is taken as main project.
        * if ``main_path`` is ``None`` but the current working directory contains a git clone,
          it is taken as main project
        * if ``main_path`` is ``None`` and the current working directory does **not** contain a git clone,
          the workspace is initialized **without** main project.
        """
        secho = secho or no_echo
        if main_path:
            # Initialize with explicit main project
            main_path = Git.find_path(path=main_path)
            path = path or main_path.parent
        else:
            # Are we in a git clone?
            try:
                # YES --> use it as main project
                main_path = Git.find_path()
                path = path or main_path.parent
            except NoGitError:
                # NO --> no main project
                path = path or Path.cwd()
        if not force:
            info = Workspace.is_init(path)
            if info:
                raise InitializedError(path, info.main_path)
            # There might be anything in the workspace if we have no clean main repo!
            if main_path:
                Workspace.check_empty(path, main_path)
        if main_path:
            name = main_path.name
            secho(f"===== {resolve_relative(main_path)} (MAIN {name!r}) =====", fg=_COLOR_BANNER)
        return GitWS.create(
            path,
            main_path=main_path,
            manifest_path=manifest_path,
            group_filters=group_filters,
            force=force,
            secho=secho,
        )

    def deinit(
        self,
        prune: bool = False,
        force: bool = False,
    ):
        """
        De-Initialize :any:`GitWS`.

        The workspace is not working anymore after that. The corresponding :any:`GitWS` instance should be deleted.

        Keyword Args:
            prune: Remove dependencies, including non-project data!
            force: Enforce to prune repositories with changes.
        """
        if prune:
            self._prune(self.workspace, force=force)
        return self.workspace.deinit()

    @staticmethod
    def check_manifest(manifest_path: Path):
        """
        Check Manifest at ``manifest_path``.

        Read in and evaluate.

        Raises:
            ManifestNotFoundError: If manifest does not exists.
            ManifestError: If manifest is broken.
        """
        manifest_spec = ManifestSpec.load(manifest_path)
        Manifest.from_spec(manifest_spec, path=str(manifest_path))

    @staticmethod
    def clone(
        url: str,
        path: Optional[Path] = None,
        main_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        revision: Optional[str] = None,
        force: bool = False,
        secho=None,
    ) -> "GitWS":
        """
        Clone git ``url``, initialize NEW Workspace and return corresponding :any:`GitWS`.

        Args:
            url: Main Project URL.

        Keyword Args:
            path: Workspace Path. Parent directory of Git Clone Root Directory by default.
            main_path: Main Project Path. Twice the URL stem in the current working directory by default.
            manifest_path: Manifest File Path. Relative to ``main_path``. Default is ``git-ws.toml``.
                           This value is written to the configuration.
            group_filters: Default Group Filters.
                           This value is written to the configuration.
            revision: Revision instead of default one.
            force: Ignore that the workspace is not empty.
            secho: :any:`click.secho` like print method for verbose output.
        """
        secho = secho or no_echo
        parsedurl = urllib.parse.urlparse(url)
        name = removesuffix(Path(parsedurl.path).name, ".git")
        if main_path is None:
            main_path = Path.cwd() / name / name
        else:
            main_path = main_path.resolve()
        main_path.parent.mkdir(parents=True, exist_ok=True)
        main_path_rel = resolve_relative(main_path)
        path = path or main_path.parent
        if not force:
            Workspace.check_empty(path, main_path)
        secho(f"===== {main_path_rel} (MAIN {name!r}) =====", fg=_COLOR_BANNER)
        secho(f"Cloning {url!r}.", fg=_COLOR_ACTION)
        clone_cache = AppConfig().options.clone_cache
        git = Git(main_path_rel, clone_cache=clone_cache, secho=secho)
        git.clone(url, revision=revision)
        return GitWS.create(
            path,
            main_path=main_path,
            manifest_path=manifest_path,
            group_filters=group_filters,
            secho=secho,
        )

    def update(
        self,
        project_paths: Optional[ProjectPaths] = None,
        skip_main: bool = False,
        prune: bool = False,
        rebase: bool = False,
        force: bool = False,
    ):
        """
        Create/Update all dependent projects.

        * Missing dependencies are cloned.
        * Existing dependencies are fetched.
        * Checkout revision from manifest
        * Merge latest upstream changes.

        Keyword Args:
            project_paths: Limit operation to these projects.
            skip_main: Exclude main project.
            prune: Remove obsolete files from workspace, including non-project data!
            rebase: Rebase instead of merge.
            force: Enforce to prune repositories with changes.
        """
        # pylint: disable=too-many-locals
        workspace = self.workspace
        main_path = workspace.info.main_path
        used: List[Path] = []
        linkfileupdater = LinkFileUpdater(workspace.path, secho=self.secho)
        copyfileupdater = CopyFileUpdater(workspace.path, secho=self.secho)
        for clone in self._foreach(project_paths=project_paths, skip_main=skip_main, resolve_url=True):
            project = clone.project
            used.append(Path(project.path))
            clone.check(diff=False, exists=False)
            self._update(clone, rebase)
            linkfileupdater.set(project.path, project.linkfiles)
            copyfileupdater.set(project.path, project.copyfiles)
        if main_path and not skip_main:
            used.append(main_path)
            manifest_spec = self.get_manifest_spec()
            main_path_str = str(workspace.info.main_path)
            linkfileupdater.set(main_path_str, manifest_spec.linkfiles)
            copyfileupdater.set(main_path_str, manifest_spec.copyfiles)
        if prune:
            self._prune(workspace, used, force=force)
        if workspace.info.project_linkfiles or workspace.info.project_copyfiles or linkfileupdater or copyfileupdater:
            # Update Links/Copies
            self.secho("===== Update Files =====", fg=_COLOR_BANNER)
            with workspace.edit_info() as info:
                # Remove all obsolete files first, to all re-map without issues
                linkfileupdater.remove(info.project_linkfiles)
                copyfileupdater.remove(info.project_copyfiles)
                linkfileupdater.update(info.project_linkfiles)
                copyfileupdater.update(info.project_copyfiles)

    def _update(self, clone: Clone, rebase: bool):
        # Clone
        project = clone.project
        git = clone.git
        if git.is_cloned():
            # Determine actual version
            tag = git.get_tag()
            branch = git.get_branch()
            sha = git.get_sha()

            if project.revision in (sha, tag) and not branch:
                self.secho("Nothing to do.", fg=_COLOR_ACTION)
            else:
                revision = branch or tag or sha

                # Checkout
                fetched = False
                if project.revision and revision != project.revision:
                    self.secho("Fetching.", fg=_COLOR_ACTION)
                    git.fetch()
                    fetched = True
                    git.checkout(project.revision)
                    branch = git.get_branch()
                    revision = branch or tag or sha

                # Pull or Rebase in case we are on a branch (or have switched to it.)
                if branch:
                    if rebase:
                        if not fetched:
                            self.secho("Fetching.", fg=_COLOR_ACTION)
                            git.fetch()
                        self.secho(f"Rebasing branch {branch!r}.", fg=_COLOR_ACTION)
                        git.rebase()
                    else:
                        if not fetched:
                            self.secho(f"Pulling branch {branch!r}.", fg=_COLOR_ACTION)
                            git.pull()
                        else:
                            self.secho(f"Merging branch {branch!r}.", fg=_COLOR_ACTION)
                            git.merge(f"origin/{branch}")

        else:
            self.secho(f"Cloning {project.url!r}.", fg=_COLOR_ACTION)
            git.clone(project.url, revision=project.revision)

        if project.submodules:
            git.submodule_update(init=True, recursive=True)

    def _prune(self, workspace: Workspace, used: Optional[List[Path]] = None, force: bool = False):
        used = used or []
        for obsolete_path in workspace.iter_obsoletes(used):
            rel_path = resolve_relative(obsolete_path)
            self.secho(f"===== {rel_path} (OBSOLETE) =====", fg=_COLOR_BANNER)
            self.secho(f"Removing {str(rel_path)!r}.", fg=_COLOR_ACTION)
            git = Git(obsolete_path, secho=self.secho)
            if force or not git.is_cloned() or git.is_empty():
                shutil.rmtree(obsolete_path, ignore_errors=True)
            else:
                raise GitCloneNotCleanError(resolve_relative(rel_path))

    def status(
        self,
        paths: Optional[Tuple[Path, ...]] = None,
        banner: bool = False,
        branch: bool = False,
    ) -> Generator[Status, None, None]:
        """
        Enriched Git Status - aka ``git status``.

        The given ``paths`` are automatically mapped to the corresponding git clones.

        Keyword Args:
            paths: Limit Git Status to ``paths`` only.
            branch: Dump branch information.

        Yields:
            :any:`Status`
        """
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            if banner:
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
            clone.check()
            path = clone.git.path
            for status in clone.git.status(paths=cpaths, branch=branch):
                yield status.with_path(path)

    def diff(self, paths: Optional[Tuple[Path, ...]] = None):
        """
        Enriched Git Diff - aka ``git diff``.

        Keyword Args:
            paths: Limit Git Diff to ``paths`` only.
        """
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
            clone.check()
            clone.git.diff(paths=cpaths, prefix=Path(clone.project.path))

    def diffstat(self, paths: Optional[Tuple[Path, ...]] = None) -> Generator[DiffStat, None, None]:
        """
        Enriched Git Diff Status - aka ``git diff --stat``.

        Keyword Args:
            paths: Limit Git Diff to ``paths`` only.

        Yields:
            :any:`DiffStat`
        """
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
            clone.check()
            path = clone.git.path
            for diffstat in clone.git.diffstat(paths=cpaths):
                yield diffstat.with_path(path)

    def checkout(self, paths: Optional[Tuple[Path, ...]] = None, force: bool = False):
        """
        Enriched Git Checkout - aka ``git checkout``.

        The given ``paths`` are automatically mapped to the corresponding git clones.

        Keyword Args:
            paths: Limit Checkout to ``paths`` only. Otherwise run checkout on all git clones.
            force: force checkout (throw away local modifications)
        """
        if paths:
            # Checkout specific files only
            for clone, cpaths in map_paths(tuple(self.clones()), paths):
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
                clone.check()
                clone.git.checkout(revision=clone.project.revision, paths=cpaths, force=force)
        else:
            # Checkout all clones
            for clone in self.clones(resolve_url=True):
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
                git = clone.git
                project = clone.project
                if not git.is_cloned():
                    self.secho(f"Cloning {project.url!r}.", fg=_COLOR_ACTION)
                    git.clone(project.url, revision=project.revision)
                if project.revision and not project.is_main:
                    git.checkout(revision=project.revision, force=force)
                clone.check(exists=False)

    def add(self, paths: Tuple[Path, ...], force: bool = False, all_: bool = False):
        """
        Add paths to index - aka ``git add``.

        The given ``paths`` are automatically mapped to the corresponding git clones.

        Args:
            paths: Paths to be added.

        Keyword Args:
            force: allow adding otherwise ignored files.
            all_: add changes from all tracked and untracked files.
        """
        if paths:
            for clone, cpaths in map_paths(tuple(self.clones()), paths):
                clone.git.check()
                clone.git.add(cpaths, force=force)
        else:
            if all_:
                for clone in self.clones():
                    clone.git.check()
                    clone.git.add(all_=True, force=force)
            else:
                raise ValueError("Nothing specified, nothing added.")

    # pylint: disable=invalid-name
    def rm(self, paths: Tuple[Path, ...], cached: bool = False, force: bool = False, recursive: bool = False):
        """
        Remove ``paths`` - aka ``git rm``

        The given ``paths`` are automatically mapped to the corresponding git clones.

        Args:
            paths: Paths.

        Keyword Args:
            cached: only remove from the index
            force: override the up-to-date check
            recursive: allow recursive removal
        """
        if not paths:
            raise ValueError("Nothing specified, nothing removed.")
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            clone.git.check()
            clone.git.rm(cpaths, cached=cached, force=force, recursive=recursive)

    def reset(self, paths: Tuple[Path, ...]):
        """
        Reset ``paths`` - aka ``git reset``.

        The given ``paths`` are automatically mapped to the corresponding git clones.
        """
        for clone, cpaths in map_paths(tuple(self.clones()), paths):
            clone.git.check()
            clone.git.reset(cpaths)

    def commit(self, msg: str, paths: Tuple[Path, ...], all_: bool = False):
        """
        Commit - aka ``git commit``.

        The given ``paths`` are automatically mapped to the corresponding git clones.

        Args:
            msg: Commit Message

        Keyword Args:
            paths: Paths.
            all_: commit all changed files
        """
        if paths:
            # clone file specific commit
            for clone, cpaths in map_paths(tuple(self.clones()), paths):
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
                clone.check()
                clone.git.commit(msg, paths=cpaths, all_=all_)
        else:
            # commit changed clones
            if all_:
                clones = [clone for clone in self.clones() if clone.git.has_changes()]
            else:
                clones = [clone for clone in self.clones() if clone.git.has_index_changes()]
            for clone in clones:
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
                clone.check()
                clone.git.commit(msg, all_=all_)

    def tag(self, name: str, msg: Optional[str] = None, force: bool = False):
        """
        Create Git Tag `name` with `msg`.

        The following steps are done to create a valid tag:

        1. store a frozen manifest to ``main_path/.git-ws/manifests/<name>.toml``
        2. commit frozen manifest from ``main_path/.git-ws/manifests/<name>.toml``
        3. create git tag.
        """
        main_path = self.main_path
        if not main_path:
            raise NoMainError()
        clone = Clone.from_project(self.workspace, next(self.projects()), secho=self.secho)
        self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
        git = clone.git
        # check
        if not force and git.get_tags(name):
            raise GitTagExistsError(name)
        # freeze
        manifest_path = MANIFESTS_PATH / f"{name}.toml"
        manifest_spec = self.get_manifest_spec(freeze=True, resolve=True)
        (main_path / MANIFESTS_PATH).mkdir(exist_ok=True, parents=True)
        (main_path / manifest_path).touch()
        manifest_spec.save(main_path / manifest_path)
        # commit
        paths = (manifest_path,)
        git.add(paths, force=True)
        git.commit(msg or name, paths=paths)
        # tag
        git.tag(name, msg=msg, force=force)

    def run_foreach(
        self,
        command,
        project_paths: Optional[ProjectPaths] = None,
        reverse: bool = False,
    ):
        """
        Run ``command`` on each clone.

        Args:
            command: Command to run

        Keyword Args:
            project_paths: Limit to projects only.
            reverse: Operate in reverse order.
        """
        for clone in self.foreach(project_paths=project_paths, reverse=reverse):
            run(command, cwd=clone.git.path)

    def foreach(
        self, project_paths: Optional[ProjectPaths] = None, resolve_url: bool = False, reverse: bool = False
    ) -> Generator[Clone, None, None]:
        """
        User Level Clone Iteration.

        We are printing the a banner for each clone.

        Keyword Args:
            project_paths: Limit to projects only.
            resolve_url: Resolve URLs to absolute ones.
            reverse: Operate in reverse order.

        Yields:
            :any:`Clone`
        """
        for clone in self._foreach(project_paths=project_paths, resolve_url=resolve_url, reverse=reverse):
            clone.check()
            yield clone

    def _foreach(
        self,
        project_paths: Optional[ProjectPaths] = None,
        skip_main: bool = False,
        resolve_url: bool = False,
        reverse: bool = False,
    ) -> Generator[Clone, None, None]:
        project_paths_filter = self._create_project_paths_filter(project_paths)
        clones = self.clones(skip_main=skip_main, resolve_url=resolve_url, reverse=reverse)
        for clone in clones:
            project = clone.project
            if project_paths_filter(project):
                self.secho(f"===== {clone.info} =====", fg=_COLOR_BANNER)
                yield clone
            else:
                self.secho(f"===== SKIPPING {clone.info} =====", fg=_COLOR_SKIP)

    def clones(
        self, skip_main: bool = False, resolve_url: bool = False, reverse: bool = False
    ) -> Generator[Clone, None, None]:
        """
        Iterate over Clones.

        Keyword Args:
            skip_main: Skip Main Repository.
            resolve_url: Resolve URLs to absolute ones.
            reverse: Operate in reverse order.

        Yields:
            :any:`Clone`
        """
        workspace = self.workspace
        projects = self.projects(skip_main=skip_main, resolve_url=resolve_url)
        if reverse:
            projects = reversed(tuple(projects))  # type: ignore
        for project in projects:
            clone = Clone.from_project(workspace, project, secho=self.secho)
            yield clone

    def projects(self, skip_main: bool = False, resolve_url: bool = False) -> Generator[Project, None, None]:
        """
        Iterate over Projects in actual workspace.

        Keyword Args:
            skip_main: Skip Main Repository.
            resolve_url: Resolve URLs to absolute ones.

        Yields:
            :any:`Project`
        """
        workspace = self.workspace
        manifest_path = self.manifest_path
        group_filters = self.group_filters
        yield from ProjectIter(workspace, manifest_path, group_filters, skip_main=skip_main, resolve_url=resolve_url)

    def manifests(
        self,
    ) -> Generator[Manifest, None, None]:
        """
        Iterate Over Manifests In Actual Workspace.
        """
        workspace = self.workspace
        manifest_path = self.manifest_path
        group_filters = self.group_filters
        yield from ManifestIter(workspace, manifest_path, group_filters)

    @staticmethod
    def create_manifest(manifest_path: Path = MANIFEST_PATH_DEFAULT) -> Path:
        """Create Manifest File at ``manifest_path``."""
        if manifest_path.exists():
            raise ManifestExistError(manifest_path)
        manifest_spec = ManifestSpec()
        manifest_spec.save(manifest_path)
        return manifest_path

    def get_manifest_spec(self, freeze: bool = False, resolve: bool = False) -> ManifestSpec:
        """
        Get Manifest Specification.

        Read the manifest file with the manifest specification.

        Keyword Args:
            freeze: Determine actual SHA of each project and use it as revision.
            resolve: Add project specification of all transient dependencies.
        """
        workspace = self.workspace
        manifest_path = self.manifest_path
        manifest_spec = ManifestSpec.load(manifest_path)
        if resolve:
            rdeps: List[ProjectSpec] = []
            for project in self.projects(skip_main=True):
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
                git = Git(resolve_relative(project_path), secho=self.secho)
                git.check()
                revision = git.get_sha()
                fdeps.append(project_spec.update(revision=revision))
            manifest_spec = manifest_spec.update(dependencies=fdeps)
        return manifest_spec

    def get_manifest(self, freeze: bool = False, resolve: bool = False) -> Manifest:
        """
        Get Manifest.

        Read the manifest file with the manifest specification and translate to manifest.

        Keyword Args:
            freeze: Determine actual SHA of each project and use it as revision.
            resolve: Add project specification of all transient dependencies.
        """
        manifest_path = self.workspace.get_manifest_path()
        manifest_spec = self.get_manifest_spec(freeze=freeze, resolve=resolve)
        return Manifest.from_spec(manifest_spec, path=str(manifest_path))

    def get_deptree(self, primary=False) -> DepNode:
        """Get Dependency Tree."""
        manifest = self.get_manifest()
        return get_deptree(self.workspace, manifest, primary=primary)

    def _create_project_paths_filter(self, project_paths: Optional[ProjectPaths]):
        if project_paths:
            workspace = self.workspace
            abspaths = [Path(project_path).resolve() for project_path in project_paths]
            return lambda project: workspace.get_project_path(project) in abspaths

        def default_filter(project: Project) -> bool:
            """Default Filter - always returning True."""
            # pylint: disable=unused-argument
            return True

        return default_filter
