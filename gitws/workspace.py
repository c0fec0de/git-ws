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
Workspace Handling.

The :any:`Workspace` class represents the location containing all git clones.
:any:`Info` is a helper.
"""
import logging
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

import tomlkit

from ._basemodel import BaseModel
from ._util import resolve_relative
from .appconfig import AppConfig, AppConfigData, AppConfigLocation
from .const import GIT_WS_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT
from .datamodel import GroupFilters, Project, WorkspaceFileRefs
from .exceptions import InitializedError, OutsideWorkspaceError, UninitializedError, WorkspaceNotEmptyError
from .workspacefinder import find_workspace

_LOGGER = logging.getLogger("git-ws")


class Info(BaseModel):
    """
    Workspace Information Container.

    The workspace information container assembles all information which has to be kept persistant between tool
    invocations.

    Keyword Args:
        main_path: Path to main project. Relative to workspace root directory.
    """

    main_path: Optional[Path] = None
    """
    Path to main project. Relative to workspace root directory.
    """

    filerefs: WorkspaceFileRefs = []
    """
    File References.

    These copied files and symbolic links have been created by GitWS and will be removed if not needed anymore.
    """

    @staticmethod
    def load(path: Path) -> "Info":
        """
        Load Workspace Information from GitWS root directory at ``path``.

        The workspace information is stored at ``{path}/.gitws/info.toml``.

        Args:
            path: Path to GitWS root directory.
        """
        infopath = path / INFO_PATH
        doc = tomlkit.parse(infopath.read_text())
        return Info(
            main_path=doc.get("main_path", None),
            filerefs=doc.get("filerefs", []),
        )

    def save(self, path: Path):
        """
        Save Workspace Information at GitWS root directory at ``path``.

        The workspace information is stored at ``{path}/.gitws/info.toml``.

        Args:
            path: Path to GitWS root directory.
        """
        infopath = path / INFO_PATH
        infopath.parent.mkdir(parents=True, exist_ok=True)
        # structure
        try:
            doc = tomlkit.parse(infopath.read_text())
        except FileNotFoundError:
            doc = tomlkit.document()
            doc.add(tomlkit.comment("Git Workspace System File. DO NOT EDIT."))
            doc.add(tomlkit.nl())
        # update
        selfdict = self.dict(exclude_none=True)
        selfdict["main_path"] = str(self.main_path) if self.main_path else None
        for name, value in selfdict.items():
            if value:
                doc[name] = value
            else:
                doc.pop(name, None)
        # write
        infopath.write_text(tomlkit.dumps(doc))


class Workspace:

    """
    Workspace.

    The workspace contains all git clones, but is *NOT* a git clone itself.
    A workspace refers to a main git clone or a standalone manifest, which defines the workspace content
    (i.e. dependencies).

    Args:
        path: Workspace Root Directory.
        info: Workspace Information.
    """

    def __init__(self, path: Path, info: Info):
        self.path = path
        self.info = info
        self.app_config = AppConfig(workspace_config_dir=str(path / GIT_WS_PATH))

    def __eq__(self, other):
        if isinstance(other, Workspace):
            return (self.path, self.info) == (other.path, other.info)
        return NotImplemented

    @staticmethod
    def find_path(path: Optional[Path] = None) -> Path:
        """
        Find Workspace Root Directory.

        Keyword Args:
            path (Path): directory or file within the workspace. Current working directory by default.

        Raises:
            UninitializedError: If directory of file is not within a workspace.

        The workspace root directory contains a sub directory ``.gitws``.
        This one is searched upwards the given ``path``.
        """
        path = find_workspace(path=path)
        if path:
            return path
        raise UninitializedError()

    @staticmethod
    def from_path(path=None) -> "Workspace":
        """
        Create :any:`Workspace` for existing workspace at ``path``.

        Keyword Args:
            path (Path): directory or file within the workspace. Current working directory by default.

        Raises:
            UninitializedError: If directory of file is not within a workspace.

        The workspace root directory contains a sub directory ``.gitws``.
        This one is searched upwards the given ``path``.
        """
        path = Workspace.find_path(path=path)
        info = Info.load(path)
        workspace = Workspace(path, info)
        _LOGGER.info("Workspace path=%s main=%s", path, info.main_path)
        _LOGGER.info("%r", workspace.config)
        return workspace

    @staticmethod
    def is_init(path: Path) -> Optional[Info]:
        """Return :any:`Info` if workspace is already initialized."""
        infopath = path / INFO_PATH
        if infopath.exists():
            return Info.load(path)
        return None

    @staticmethod
    def check_empty(path: Path, main_path: Optional[Path]):
        """Check if Workspace at ``path`` with ``main_path`` is empty."""
        items = [item for item in path.iterdir() if item != main_path]
        if any(items):
            raise WorkspaceNotEmptyError(resolve_relative(path), items)

    @staticmethod
    def init(
        path: Path,
        main_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        depth: Optional[int] = None,
        force: bool = False,
    ) -> "Workspace":
        """
        Initialize new :any:`Workspace` at ``path``.

        Args:
            path:  Path to the workspace

        Keyword Args:
            main_path:  Path to the main project. Relative to ``path``.
            manifest_path:  Path to the manifest file. Relative to ``main_path`` or ``path``.
                            Default is ``git-ws.toml``.
            group_filters: Group Filters.
            depth: Shallow Clone Depth.
            force: Ignore that the workspace exists.

        Raises:
            InitializedError: ``path`` already contains workspace.
            OutsideWorkspaceError: ``main_path`` is not within ``path``.
        """
        if not force:
            info = Workspace.is_init(path)
            if info:
                raise InitializedError(path, info.main_path)

        # Normalize
        if main_path:
            try:
                main_path = (path / main_path).resolve().relative_to(path.resolve())
            except ValueError:
                raise OutsideWorkspaceError(path, main_path, "Project") from None

        # Initialize Info
        info = Info(main_path=main_path)
        info.save(path)
        workspace = Workspace(path.resolve(), info)
        with workspace.app_config.edit(AppConfigLocation.WORKSPACE) as config:
            config.manifest_path = str(manifest_path or MANIFEST_PATH_DEFAULT)
            config.group_filters = group_filters
            config.depth = depth
        _LOGGER.info("Workspace path=%s main=%s", path, info.main_path)
        _LOGGER.info("%r", workspace.config)
        return workspace

    def deinit(self):
        """
        Deinitialize.

        Remove ``GIT_WS_PATH`` directory.
        """
        shutil.rmtree(self.path / GIT_WS_PATH)

    @property
    def main_path(self) -> Optional[Path]:
        """Resolved Path To Main Project."""
        info_main_path = self.info.main_path
        if info_main_path:
            return self.path / info_main_path
        return None

    @property
    def base_path(self) -> Path:
        """Resolved Path To Main Project Or Workspace."""
        info_main_path = self.info.main_path
        if info_main_path:
            return self.path / info_main_path
        return self.path

    @property
    def config(self) -> AppConfigData:
        """Application Configuration Values."""
        return self.app_config.options

    def get_project_path(self, project: Project, relative: bool = False) -> Path:
        """
        Determine Project Path.

        Args:
            project: Project to determine path for.

        Keyword Args:
            relative: Return relative instead of absolute path.
        """
        project_path = self.path / project.path
        if relative:
            project_path = resolve_relative(project_path)
        return project_path

    def get_manifest_path(self, manifest_path: Optional[Path] = None) -> Path:
        """
        Get Resolved Manifest Path.

        Keyword Args:
            manifest_path: Absolute Or Relative (To ``self.base_path``) Manifest Path.

        The manifest path is choosen according to the following list, the first matching wins:

        * Explicit manifest path specified by ``manifest_path``.
        * Path from configuration (set during ``init``, ``clone`` or later on).
        * ``git-ws.toml`` (default)
        """
        return self.base_path / (manifest_path or self.app_config.options.manifest_path or MANIFEST_PATH_DEFAULT)

    def get_group_filters(self, group_filters: Optional[GroupFilters] = None) -> GroupFilters:
        """
        Get Group Filters.

        Keyword Args:
            group_filters: Group Filters.

        The group filter is choosen according to the following list, the first matching wins:

        * Explicit group filter specified by ``group_filters``.
        * Path from configuration (set during ``init``, ``clone`` or later on).
        * empty group filters.
        """
        if group_filters is None:
            return self.app_config.options.group_filters or GroupFilters()
        return group_filters

    @contextmanager
    def edit_info(self) -> Generator[Info, None, None]:
        """Yield Contextmanager to edit :any:`Info` and write back changes."""
        try:
            yield self.info
        finally:
            self.info.save(self.path)
