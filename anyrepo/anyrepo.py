"""
Multi Repository Management.
"""

import logging
import pathlib
from typing import Optional

from pydantic import BaseModel

from ._git import get_repo_top
from ._util import no_banner, run
from .exceptions import UninitializedError
from .manifest import Project, create_project_filter

CONFIG_FILE = ".anyrepo"
_LOGGER = logging.getLogger("anyrepo")


class AnyRepo(BaseModel):
    """
    Multi Repository Management.

    :param root_path: Path to the AnyRepo Root.
    """

    root_path: pathlib.Path

    @staticmethod
    def find_root_path(path: Optional[pathlib.Path] = None):
        """Find anyrepo root directory."""
        spath = path or pathlib.Path.cwd()
        while True:
            configpath = spath / CONFIG_FILE
            if configpath.exists():
                return spath
            if spath == spath.parent:
                break
            spath = spath.parent
        raise UninitializedError()

    @staticmethod
    def from_path(path=None) -> "AnyRepo":
        """
        Create :any:`AnyRepo`.

        :param path:  Path within the workspace (Default is the current working directory).
        """
        root_path = AnyRepo.find_root_path(path=path)
        _LOGGER.info("root_path=%s", root_path)
        return AnyRepo.from_root_path(root_path)

    @staticmethod
    def from_root_path(root_path) -> "AnyRepo":
        """
        Create :any:`AnyRepo`.

        :param root_path: The path to the workspace's root project.
        """
        return AnyRepo(root_path=root_path)

    @staticmethod
    def init(clone_path=None) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `clone_path`.

        :param clone_path: Path within git clone. (Default is the current working directory).
        """
        repo_top = get_repo_top(path=clone_path)
        # TODO: read manifest and check path
        root_path = repo_top.parent
        AnyRepo._init(root_path)
        return AnyRepo.from_root_path(root_path)

    @staticmethod
    def clone(url) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        assert False, "TODO"
        return AnyRepo()

    def update(self, project_paths=None, banner=None):
        """Create/Update all dependent projects."""
        for project in self.iter_projects(project_paths=project_paths, banner=banner):
            self._update(project)

    def foreach(self, command, project_paths=None, banner=None):
        """Run `command` on each project."""
        for project in self.iter_projects(project_paths=project_paths, banner=banner):
            path = self.root_path / project.path
            run(command, cwd=path)

    def iter_projects(self, project_paths=None, banner=None):
        """
        Iterate Over Projects and yield them.

        :param project_paths: Only yield projects at these paths.
        :param banner: Print method for project banner.
        """
        project_paths = [self.get_subpath(path) for path in project_paths]
        filter_ = create_project_filter(project_paths=project_paths)
        banner = banner or no_banner
        for project in self._iter_projects(filter_=filter_):
            banner(f"{project.name} ({project.path})")
            yield project

    def _iter_projects(self, filter_=None):
        """Iterate over all projects."""
        yield Project(name="main", path="main")

    @staticmethod
    def _init(root_path):
        # TODO:
        config_path = root_path / CONFIG_FILE
        config_path.touch()

    def _update(self, project):
        """Update."""

    def get_subpath(self, path):
        """Return `path` relative to workspace."""
        path = self.root_path / pathlib.Path(path)
        return path.relative_to(self.root_path)
