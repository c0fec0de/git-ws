"""
Multi Repository Management.

The :any:`AnyRepo` class provides a simple facade to all inner `AnyRepo` functionality.
"""
import logging
import shlex
import shutil
import urllib
from pathlib import Path
from typing import Generator, List, Optional

from ._git import Git, get_repo_top
from ._util import no_colorprint, resolve_relative, run
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestExistError
from .filters import Filter, default_filter
from .iters import ManifestIter, ProjectIter
from .manifest import Manifest, ManifestSpec, Project, ProjectSpec
from .types import Groups, ProjectFilter
from .workspace import Workspace

_LOGGER = logging.getLogger("anyrepo")
_COLOR_BANNER = "green"
_COLOR_ACTION = "magenta"
_COLOR_SKIP = "blue"


class AnyRepo:
    """
    Multi Repository Management.

    Args:
        workspace (Workspace): workspace.
        manifest_spec (ManifestSpec): manifest.
    """

    def __init__(self, workspace: Workspace, manifest_spec: ManifestSpec, colorprint=None):
        self.workspace = workspace
        self.manifest_spec = manifest_spec
        self.colorprint = colorprint or no_colorprint

    def __eq__(self, other):
        if isinstance(other, AnyRepo):
            return (self.workspace, self.manifest_spec) == (other.workspace, other.manifest_spec)
        return NotImplemented

    @property
    def path(self) -> Path:
        """
        AnyRepo Workspace Root Directory.
        """
        return self.workspace.path

    @staticmethod
    def from_path(path: Optional[Path] = None, manifest_path: Optional[Path] = None, colorprint=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        return AnyRepo(workspace, manifest_spec, colorprint=colorprint)

    @staticmethod
    def create(
        path: Path, project_path: Path, manifest_path: Path, groups: Groups = None, colorprint=None
    ) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
            project_path:  Main Project Path.
            mainfest_path:  ManifestSpec File Path.
        """
        manifest_path = project_path / manifest_path
        manifest_spec = ManifestSpec.load(manifest_path)
        workspace = Workspace.init(
            path, project_path, resolve_relative(manifest_path, base=project_path), groups=groups
        )
        return AnyRepo(workspace, manifest_spec, colorprint=colorprint)

    @staticmethod
    def init(
        project_path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
        groups: Groups = None,
        colorprint=None,
    ) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `project_path`.

        :param project_path: Path within git clone. (Default is the current working directory).
        :param manifest_path: Path to the manifest file.
        """
        colorprint = colorprint or no_colorprint
        project_path = get_repo_top(path=project_path)
        name = project_path.name
        colorprint(f"===== {name} (revision=None, path={name!r}) =====", fg=_COLOR_BANNER)
        manifest_path = resolve_relative(project_path / manifest_path)
        path = project_path.parent
        return AnyRepo.create(path, project_path, manifest_path, groups, colorprint=colorprint)

    @staticmethod
    def clone(
        url: str,
        path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
        groups: Groups = None,
        colorprint=None,
    ) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        colorprint = colorprint or no_colorprint
        path = path or Path.cwd()
        parsedurl = urllib.parse.urlparse(url)
        name = Path(parsedurl.path).name
        colorprint(f"===== {name} (revision=None, path={name!r}) =====", fg=_COLOR_BANNER)
        colorprint(f"Cloning {url!r}.", fg=_COLOR_ACTION)
        project_path = path / name
        git = Git(project_path)
        git.clone(url)
        return AnyRepo.create(path, project_path, manifest_path, groups, colorprint=colorprint)

    def update(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        prune: bool = False,
        rebase: bool = False,
    ):
        """Create/Update all dependent projects."""
        workspace = self.workspace
        used: List[Path] = [workspace.info.main_path]
        for project in self.iter(
            project_paths=project_paths, manifest_path=manifest_path, groups=groups, skip_main=True, resolve_url=True
        ):
            used.append(Path(project.path))
            project_path = workspace.get_project_path(project, relative=True)
            git = Git(project_path)
            self._update(git, project, rebase)
        if prune:
            self._prune(workspace, used)

    def _update(self, git, project, rebase):
        # Clone
        if not git.is_cloned():
            self.colorprint(f"Cloning {project.url!r}.", fg=_COLOR_ACTION)
            git.clone(project.url, revision=project.revision)
            return

        # Determine actual version
        sha = git.get_sha()
        tag = git.get_tag()
        branch = git.get_branch()

        if project.revision in (sha, tag) and not branch:
            self.colorprint("Nothing to do.", fg=_COLOR_ACTION)
            return

        revision = branch or tag or sha

        # Checkout
        fetched = False
        if project.revision and revision != project.revision:
            self.colorprint("Fetching.", fg=_COLOR_ACTION)
            git.fetch()
            fetched = True
            self.colorprint(f"Checking out {project.revision!r} (previously {revision!r}).", fg=_COLOR_ACTION)
            git.checkout(project.revision)
            branch = git.get_branch()
            revision = branch or tag or sha

        # Pull or Rebase in case we are on a branch (or have switched to it.)
        if branch:
            if rebase:
                if not fetched:
                    self.colorprint("Fetching.", fg=_COLOR_ACTION)
                    git.fetch()
                self.colorprint(f"Rebasing branch {branch!r}.", fg=_COLOR_ACTION)
                git.rebase()
            else:
                if not fetched:
                    self.colorprint(f"Pulling branch {branch!r}.", fg=_COLOR_ACTION)
                    git.pull()
                else:
                    self.colorprint(f"Merging branch {branch!r}.", fg=_COLOR_ACTION)
                    git.merge()

    def _prune(self, workspace: Workspace, used: List[Path]):
        for obsolete_path in workspace.iter_obsoletes(used):
            name = resolve_relative(obsolete_path, workspace.path)
            self.colorprint(f"===== {name} (OBSOLETE) =====", fg=_COLOR_BANNER)
            self.colorprint(f"Removing {str(obsolete_path)!r}.", fg=_COLOR_ACTION)
            # TODO: safety check.
            shutil.rmtree(obsolete_path, ignore_errors=True)

    def foreach(self, command, project_paths=None, manifest_path: Path = None, groups: Groups = None):
        """Run `command` on each project."""
        workspace = self.workspace
        for project in self.iter(project_paths=project_paths, manifest_path=manifest_path, groups=groups):
            cmdstr = " ".join(shlex.quote(part) for part in command)
            self.colorprint(cmdstr, fg=_COLOR_ACTION)
            project_path = workspace.get_project_path(project, relative=True)
            run(command, cwd=project_path)

    def iter(
        self,
        project_paths=None,
        manifest_path: Path = None,
        groups: Groups = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ) -> Generator[Project, None, None]:
        """Create/Update all dependent projects."""
        project_paths_filter = self._create_project_paths_filter(project_paths)
        filter_ = self._create_groups_filter(groups)
        for project in self.iter_projects(manifest_path, filter_=filter_, skip_main=skip_main, resolve_url=resolve_url):
            self._banner(project)
            if project_paths_filter(project):
                yield project
            else:
                self.colorprint("SKIPPING", fg=_COLOR_SKIP)

    def iter_projects(
        self,
        manifest_path: Optional[Path] = None,
        filter_: ProjectFilter = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ) -> Generator[Project, None, None]:
        """Iterate over Projects."""
        workspace = self.workspace
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        yield from ProjectIter(workspace, manifest_path, filter_=filter_, skip_main=skip_main, resolve_url=resolve_url)

    def iter_manifests(
        self, manifest_path: Optional[Path] = None, filter_: ProjectFilter = None
    ) -> Generator[Manifest, None, None]:
        """Iterate over Manifests."""
        workspace = self.workspace
        manifest_path = workspace.get_manifest_path(manifest_path=manifest_path)
        yield from ManifestIter(workspace, manifest_path, filter_=filter_)

    @staticmethod
    def create_manifest(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> Path:
        """Create ManifestSpec File at `manifest_path`within `project`."""
        git = Git.from_path(path=project_path)
        manifest_path = resolve_relative(git.path / manifest_path)
        if manifest_path.exists():
            raise ManifestExistError(manifest_path)
        manifest_spec = ManifestSpec()
        manifest_spec.save(manifest_path)
        return manifest_path

    def get_manifest_spec(self, freeze: bool = False, resolve: bool = False) -> ManifestSpec:
        """Get Manifest."""
        workspace = self.workspace
        if resolve:
            rdeps: List[ProjectSpec] = []
            for project in self.iter_projects(skip_main=True):
                project_spec = ProjectSpec.from_project(project)
                rdeps.append(project_spec)
            manifest_spec = self.manifest_spec.new(dependencies=rdeps)
        else:
            manifest_spec = self.manifest_spec.copy()
        if freeze:
            manifest = Manifest.from_spec(manifest_spec)
            fdeps: List[ProjectSpec] = []
            for project_spec, project in zip(manifest_spec.dependencies, manifest.dependencies):
                project_path = workspace.get_project_path(project)
                git = Git(project_path)
                revision = git.get_tag() or git.get_sha()
                fdeps.append(project_spec.new(revision=revision))
            manifest_spec = manifest_spec.new(dependencies=fdeps)
        return manifest_spec

    def get_manifest(self, freeze: bool = False, resolve: bool = False) -> Manifest:
        """Get Manifest."""
        manifest_path = self.workspace.get_manifest_path()
        manifest_spec = self.get_manifest_spec(freeze=freeze, resolve=resolve)
        return Manifest.from_spec(manifest_spec, path=str(manifest_path))

    def _banner(self, project):
        project_path = resolve_relative(self.workspace.path / project.path)
        name = project.name
        revision = project.revision
        self.colorprint(f"===== {name} (revision={revision!r}, path={str(project_path)!r}) =====", fg=_COLOR_BANNER)

    def _create_project_paths_filter(self, project_paths):
        workspace_path = self.workspace.path
        if project_paths:
            project_paths = [resolve_relative(workspace_path / path, base=workspace_path) for path in project_paths]
            return lambda project: resolve_relative(workspace_path / project.path, base=workspace_path) in project_paths
        return default_filter

    def _create_groups_filter(self, groups):
        groups = self.workspace.get_groups(groups)
        if groups:
            filter_ = Filter.from_str(groups)
            return lambda project: filter_(project.groups)
        return None
