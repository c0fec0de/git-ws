"""
Multi Repository Management.

The :any:`AnyRepo` class provides a simple facade to all inner `AnyRepo` functionality.
"""
import logging
import shlex
import urllib
from pathlib import Path
from typing import Callable, Optional

from ._git import Git, get_repo_top
from ._util import no_banner, resolve_relative, run
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestExistError
from .manifest import Manifest
from .projectiter import ProjectIter
from .workspace import Workspace

_LOGGER = logging.getLogger("anyrepo")


class AnyRepo:
    """
    Multi Repository Management.

    Args:
        workspace (Workspace): workspace.
        manifest (Manifest): manifest.
    """

    def __init__(self, workspace: Workspace, manifest: Manifest, banner: Callable[[str], None] = None):
        self.workspace = workspace
        self.manifest = manifest
        self.banner: Callable[[str], None] = banner or no_banner

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
    def from_path(path: Optional[Path] = None, banner: Callable[[str], None] = None) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        manifest_path = workspace.path / workspace.info.main_path / workspace.info.manifest_path
        manifest = Manifest.load(manifest_path)
        return AnyRepo(workspace, manifest, banner=banner)

    @staticmethod
    def from_paths(
        path: Path, project_path: Path, manifest_path: Path, banner: Callable[[str], None] = None
    ) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
            project_path:  Main Project Path.
            mainfest_path:  Manifest File Path.
        """
        manifest_path = resolve_relative(project_path / manifest_path)
        manifest = Manifest.load(manifest_path)
        workspace = Workspace.init(path, project_path, manifest_path)
        return AnyRepo(workspace, manifest, banner=banner)

    @staticmethod
    def init(
        project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT, banner: Callable[[str], None] = None
    ) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `project_path`.

        :param project_path: Path within git clone. (Default is the current working directory).
        :param manifest_path: Path to the manifest file.
        """
        banner = banner or no_banner
        project_path = get_repo_top(path=project_path)
        name = project_path.name
        banner(f"{name} (revision=None, path={name})")
        manifest_path = resolve_relative(project_path / manifest_path)
        path = project_path.parent
        return AnyRepo.from_paths(path, project_path, manifest_path, banner=banner)

    @staticmethod
    def clone(
        url: str, path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT, banner: Callable[[str], None] = None
    ) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        banner = banner or no_banner
        path = path or Path.cwd()
        parsedurl = urllib.parse.urlparse(url)
        name = Path(parsedurl.path).name
        banner(f"{name} (revision=None, path={name})")
        project_path = path / name
        git = Git(project_path)
        git.clone(url)
        return AnyRepo.from_paths(path, project_path, manifest_path, banner=banner)

    def update(self, project_paths=None, manifest_path: Path = MANIFEST_PATH_DEFAULT, prune=False):
        """Create/Update all dependent projects."""
        assert not prune, "TODO"
        workspace = self.workspace
        manifest = Manifest.load(workspace.main_path / manifest_path, default=Manifest())
        for rproject in ProjectIter(workspace, manifest, skip_main=True, resolve_url=True):
            self.banner(f"{rproject.name} (revision={rproject.revision}, path={rproject.path})")
            project_path = resolve_relative(workspace.path / rproject.path)
            git = Git(project_path)
            if not git.is_cloned():
                git.clone(rproject.url, branch=rproject.revision)
            elif rproject.revision:
                git.checkout(rproject.revision)

    def foreach(self, command, project_paths=None, manifest_path: Path = MANIFEST_PATH_DEFAULT):
        """Run `command` on each project."""
        workspace = self.workspace
        manifest = Manifest.load(workspace.main_path / manifest_path, default=Manifest())
        for rproject in ProjectIter(workspace, manifest, resolve_url=True):
            self.banner(f"{rproject.name} (revision={rproject.revision}, path={rproject.path})")
            project_path = resolve_relative(workspace.path / rproject.path)
            print(shlex.join(command))
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
