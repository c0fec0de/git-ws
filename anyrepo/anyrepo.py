"""
Multi Repository Management.

The :any:`AnyRepo` class provides a simple facade to all inner `AnyRepo` functionality.
"""
import logging
import shlex
import urllib
from pathlib import Path
from typing import Generator, Optional

from ._git import Git, get_repo_top
from ._util import no_colorprint, resolve_relative, run
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestExistError
from .iters import ManifestIter, ProjectIter
from .manifest import Manifest, Project
from .workspace import Workspace

_LOGGER = logging.getLogger("anyrepo")
_COLOR_BANNER = "green"
_COLOR_ACTION = "magenta"


class AnyRepo:
    """
    Multi Repository Management.

    Args:
        workspace (Workspace): workspace.
        manifest (Manifest): manifest.
    """

    def __init__(self, workspace: Workspace, manifest: Manifest, colorprint=None):
        self.workspace = workspace
        self.manifest = manifest
        self.colorprint = colorprint or no_colorprint

    def __eq__(self, other):
        if isinstance(other, AnyRepo):
            return (self.workspace, self.manifest) == (other.workspace, other.manifest)
        return NotImplemented

    @property
    def path(self) -> Path:
        """
        AnyRepo Workspace Root Directory.
        """
        return self.workspace.path

    @staticmethod
    def from_path(path: Optional[Path] = None, colorprint=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        manifest_path = workspace.path / workspace.info.main_path / workspace.info.manifest_path
        manifest = Manifest.load(manifest_path)
        return AnyRepo(workspace, manifest, colorprint=colorprint)

    @staticmethod
    def from_paths(path: Path, project_path: Path, manifest_path: Path, colorprint=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
            project_path:  Main Project Path.
            mainfest_path:  Manifest File Path.
        """
        manifest_path = project_path / manifest_path
        manifest = Manifest.load(manifest_path)
        workspace = Workspace.init(path, project_path, resolve_relative(manifest_path, base=project_path))
        return AnyRepo(workspace, manifest, colorprint=colorprint)

    @staticmethod
    def init(
        project_path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
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
        colorprint(f"===== {name} (revision=None, path={name}) =====", fg=_COLOR_BANNER)
        manifest_path = resolve_relative(project_path / manifest_path)
        path = project_path.parent
        return AnyRepo.from_paths(path, project_path, manifest_path, colorprint=colorprint)

    @staticmethod
    def clone(
        url: str,
        path: Path = None,
        manifest_path: Path = MANIFEST_PATH_DEFAULT,
        colorprint=None,
    ) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        colorprint = colorprint or no_colorprint
        path = path or Path.cwd()
        parsedurl = urllib.parse.urlparse(url)
        name = Path(parsedurl.path).name
        colorprint(f"===== {name} (revision=None, path={name}) =====", fg=_COLOR_BANNER)
        colorprint(f"Cloning {url}.", fg=_COLOR_ACTION)
        project_path = path / name
        git = Git(project_path)
        git.clone(url)
        return AnyRepo.from_paths(path, project_path, manifest_path, colorprint=colorprint)

    def update(self, project_paths=None, manifest_path: Path = MANIFEST_PATH_DEFAULT, prune=False, rebase=False):
        """Create/Update all dependent projects."""
        assert not prune, "TODO"
        workspace = self.workspace
        for project in ProjectIter(workspace, workspace.main_path / manifest_path, skip_main=True, resolve_url=True):
            project_path = resolve_relative(workspace.path / project.path)
            self.colorprint(
                f"===== {project.name} (revision={project.revision}, path={project_path}) =====", fg=_COLOR_BANNER
            )
            git = Git(project_path)
            self._update(git, project, rebase)

    def _update(self, git, project, rebase):
        revision = project.revision
        if not git.is_cloned():
            self.colorprint(f"Cloning {project.url}.", fg=_COLOR_ACTION)
            git.clone(project.url, revision=revision)
        else:
            if revision:
                self.colorprint("Checking out.", fg=_COLOR_ACTION)
                git.checkout(revision)
            if git.is_branch(revision=revision):
                if rebase:
                    self.colorprint("Rebasing.", fg=_COLOR_ACTION)
                    git.rebase()
                else:
                    self.colorprint("Pulling.", fg=_COLOR_ACTION)
                    git.pull()
            else:
                self.colorprint("Nothing to do.", fg=_COLOR_ACTION)

    def foreach(self, command, project_paths=None, manifest_path: Path = None):
        """Run `command` on each project."""
        workspace = self.workspace
        for project in self.iter_projects(manifest_path=manifest_path):
            self.colorprint(
                f"===== {project.name} (revision={project.revision}, path={project.path}) =====", fg=_COLOR_BANNER
            )
            project_path = resolve_relative(workspace.path / project.path)
            cmdstr = " ".join(shlex.quote(part) for part in command)
            self.colorprint(cmdstr, fg=_COLOR_ACTION)
            run(command, cwd=project_path)

    @staticmethod
    def create_manifest(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> Path:
        """Create Manifest File at `manifest_path`within `project`."""
        git = Git.from_path(path=project_path)
        manifest_path = resolve_relative(git.path / manifest_path)
        if manifest_path.exists():
            raise ManifestExistError(manifest_path)
        manifest = Manifest()
        manifest.save(manifest_path)
        return manifest_path

    def iter_projects(self, manifest_path=None) -> Generator[Project, None, None]:
        """Iterate over Projects."""
        workspace = self.workspace
        manifest_path = manifest_path or workspace.info.manifest_path
        yield from ProjectIter(workspace, workspace.main_path / manifest_path)

    def iter_manifests(self, manifest_path=None):
        """Iterate over Manifests."""
        workspace = self.workspace
        manifest_path = manifest_path or workspace.info.manifest_path
        yield from ManifestIter(workspace, workspace.main_path / manifest_path)

    def get_manifest(self, freeze: bool = False, resolve: bool = False) -> Manifest:
        """Get Manifest."""
        manifest = Manifest()
        return manifest
