"""
Multi Repository Management.
"""

import logging
from pathlib import Path

# from ._git import get_repo_top
from ._util import no_banner, resolve_relative, run
from .const import MANIFEST_PATH_DEFAULT
from .manifest import Manifest, Project, create_project_filter
from .workspace import Workspace

CONFIG_FILE = ".anyrepo"
_LOGGER = logging.getLogger("anyrepo")


class AnyRepo:
    """
    Multi Repository Management.

    :param workspace (Workspace): workspace.
    """

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    @property
    def path(self):
        """
        AnyRepo Workspace Root Directory.
        """
        return self.workspace.path

    @staticmethod
    def from_path(path=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo`.

        :param path:  Path within the workspace (Default is the current working directory).
        """
        workspace = Workspace.from_path(path=path)
        return AnyRepo(workspace)

    @staticmethod
    def init(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `project_path`.

        :param project_path: Path within git clone. (Default is the current working directory).
        :param manifest_path: Path to the manifest file.
        """
        assert False, "TODO"

        # project_path = resolve_relative(get_repo_top(path=project_path))
        # manifest_path = resolve_relative(manifest_path)
        # manifest = Manifest.load(manifest_path)
        # print(manifest)
        # # TODO: read manifest and check path
        # path = project_path.parent
        # # manifest_path = MANIFEST_PATH_DEFAULT
        # workspace = Workspace.init(path, project_path, manifest_path)
        # return AnyRepo(workspace)

    @staticmethod
    def clone(url) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        assert False, "TODO"
        # return AnyRepo()

    def update(self, project_paths=None, prune=False, banner=None):
        """Create/Update all dependent projects."""
        for project in self.iter_projects(project_paths=project_paths, banner=banner):
            self._update(project)

    def foreach(self, command, project_paths=None, banner=None):
        """Run `command` on each project."""
        for project in self.iter_projects(project_paths=project_paths, banner=banner):
            path = resolve_relative(Path(project.path), base=self.path)
            run(command, cwd=path)

    @staticmethod
    def create_manifest(project_path: Path = None, manifest_path: Path = MANIFEST_PATH_DEFAULT):
        """Create Manifest File at `manifest_path`within `project`."""
        assert False, "TODO"
        # project_path = get_repo_top(path=project_path)
        # manifest_path = resolve_relative(manifest_path)
        # if manifest_path.exists():
        #     raise ManifestExistError(manifest_path)
        # print(manifest_path)
        # # path = resolve_relative(manifest_path, base=project_path)
        # manifest = Manifest(path=path)
        # manifest.save(project_path)

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

    def _update(self, project):
        """Update."""


def parse_manifest(text: str) -> Manifest:
    """Parse Manifest."""
