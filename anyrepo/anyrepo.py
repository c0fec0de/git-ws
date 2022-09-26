"""
Multi Repository Management.

The :any:`AnyRepo` class provides a simple facade to all inner `AnyRepo` functionality.
"""
import logging
import urllib
from pathlib import Path

from ._git import Git, get_repo_top
from ._util import no_banner, path_upwards, resolve_relative, run
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestError, ManifestExistError
from .manifest import Manifest, Project, create_project_filter
from .workspace import Workspace

_LOGGER = logging.getLogger("anyrepo")


class AnyRepo:
    """
    Multi Repository Management.

    Args:
        workspace (Workspace): workspace.
        manifest (Manifest): manifest.
    """

    def __init__(self, workspace: Workspace, manifest: Manifest):
        self.workspace = workspace
        self.manifest = manifest

    def __eq__(self, other):
        if isinstance(other, AnyRepo):
            return (self.workspace, self.manifest) == (other.workspace, other.manifest)
        return NotImplemented

    @property
    def path(self):
        """
        AnyRepo Workspace Root Directory.
        """
        return self.workspace.path

    @staticmethod
    def from_path(path=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo` for workspace at `path`.

        :param path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        manifest_path = workspace.path / workspace.info.main_path / workspace.info.manifest_path
        manifest = Manifest.load(manifest_path)
        return AnyRepo(workspace, manifest)

    @staticmethod
    def init(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `project_path`.

        :param project_path: Path within git clone. (Default is the current working directory).
        :param manifest_path: Path to the manifest file.
        """
        project_path = get_repo_top(path=project_path)
        manifest_path = resolve_relative(project_path / manifest_path)
        manifest = Manifest.load(manifest_path)
        try:
            path = path_upwards(project_path, Path(manifest.path or project_path.name))
        except ValueError:
            msg = f"git clone has NOT been created at path specified by manifest path={manifest.path}"
            raise ManifestError(msg) from None
        workspace = Workspace.init(path, project_path, manifest_path)
        return AnyRepo(workspace, manifest)

    @staticmethod
    def clone(url: str, path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        path = path or Path.cwd()
        parsedurl = urllib.parse.urlparse(url)
        name = Path(parsedurl.path).name
        project_path = path / name
        git = Git(project_path)
        git.clone(url)
        manifest_path = resolve_relative(project_path / manifest_path)
        manifest = Manifest.load(manifest_path)
        workspace = Workspace.init(path, project_path, manifest_path)
        return AnyRepo(workspace, manifest)

    def update(self, project_paths=None, manifest_path: Path = MANIFEST_PATH_DEFAULT, prune=False, banner=None):
        """Create/Update all dependent projects."""
        # for project in self.iter_projects(project_paths=project_paths, banner=banner):
        #     _update(workspace, project)

    def foreach(self, command, project_paths=None, banner=None):
        """Run `command` on each project."""
        for project in self.iter_projects(project_paths=project_paths, banner=banner):
            path = resolve_relative(Path(project.path), base=self.path)
            run(command, cwd=path)

    @staticmethod
    def create_manifest(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> Path:
        """Create Manifest File at `manifest_path`within `project`."""
        git = Git.from_path(path=project_path)
        manifest_path = resolve_relative(git.path / manifest_path)
        if manifest_path.exists():
            raise ManifestExistError(manifest_path)
        name = git.path.name
        revision = git.get_revision()
        main = Project(name=name, revision=revision)
        manifest = Manifest(main=main)
        manifest.save(manifest_path)
        return manifest_path

    def iter_projects(self, project_paths=None, banner=None):
        """
        Iterate Over Projects and yield them.

        :param project_paths: Only yield projects at these paths.
        :param banner: Print method for project banner.
        """
        project_paths = [resolve_relative(Path(path), base=self.path) for path in project_paths]
        filter_ = create_project_filter(project_paths=project_paths)
        banner = banner or no_banner
        for project in self._iter_projects(filter_=filter_):
            banner(f"{project.name} ({project.path})")
            yield project

    def _iter_projects(self, filter_=None):
        """Iterate over all projects."""
        yield Project(name="main", path="main")
