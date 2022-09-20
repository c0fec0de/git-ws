"""
Multi Repository Management.
"""

import logging
import pathlib

from pydantic import BaseModel

from ._util import no_banner, run
from .exceptions import UninitializedError
from .git import get_repotop
from .manifest import Project, create_project_filter

CONFIGFILE = ".anyrepo"
_LOGGER = logging.getLogger("anyrepo")


class AnyRepo(BaseModel):
    """
    Multi Repository Management.

    Args:
        rootpath: Path to the AnyRepo Root.
    """

    rootpath: pathlib.Path

    @staticmethod
    def find_rootpath(path=None):
        """Find anyrepo root directory."""
        spath = path or pathlib.Path.cwd()
        while True:
            configpath = spath / CONFIGFILE
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

        Keyword Args:
            path:  Path within the workspace (Default is the current working directory).
        """
        rootpath = AnyRepo.find_rootpath(path=path)
        _LOGGER.info("rootpath=%s", rootpath)
        return AnyRepo.from_rootpath(rootpath)

    @staticmethod
    def from_rootpath(rootpath) -> "AnyRepo":
        """
        Create :any:`AnyRepo`.

        Args:
            rootpath: Rootpath.
        """
        return AnyRepo(rootpath=rootpath)

    @staticmethod
    def init(clonepath=None) -> "AnyRepo":
        """
        Initialize Workspace for git clone at `clonepath`.

        Keyword Args:
            clonepath: Path within git clone. (Default is the current working directory).
        """
        repotop = get_repotop(path=clonepath)
        # TODO: read manifest and check path
        rootpath = repotop.parent
        AnyRepo._init(rootpath)
        return AnyRepo.from_rootpath(rootpath)

    @staticmethod
    def clone(url) -> "AnyRepo":
        """Clone git `url` and initialize Workspace."""
        assert False, "TODO"
        return AnyRepo()

    def update(self, projectpaths=None, banner=None):
        """Create/Update all dependent projects."""
        for project in self.iter_projects(projectpaths=projectpaths, banner=banner):
            self._update(project)

    def foreach(self, command, projectpaths=None, banner=None):
        """Run `command` on each project."""
        for project in self.iter_projects(projectpaths=projectpaths, banner=banner):
            path = self.rootpath / project.path
            run(command, cwd=path)

    def iter_projects(self, projectpaths=None, banner=None):
        """
        Iterate Over Projects and yield them.

        Keyword Args:
            projectpaths: Only yield projects at these paths.
            banner: Print method for project banner.
        """
        projectpaths = [self.get_subpath(path) for path in projectpaths]
        filter_ = create_project_filter(projectpaths=projectpaths)
        banner = banner or no_banner
        for project in self._iter_projects(filter_=filter_):
            banner(f"{project.name} ({project.path})")
            yield project

    def _iter_projects(self, filter_=None):
        """Iterate over all projects."""
        yield Project(name="main", path="main")

    @staticmethod
    def _init(rootpath):
        # TODO:
        configpath = rootpath / CONFIGFILE
        configpath.touch()

    def _update(self, project):
        """Update."""

    def get_subpath(self, path):
        """Return `path` relative to workspace."""
        path = self.rootpath / pathlib.Path(path)
        return path.relative_to(self.rootpath)
