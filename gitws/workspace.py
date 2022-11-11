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
Workspace Handling.

The :any:`Workspace` class represents the file system location containing all git clones.
:any:`Info` is a helper.
"""
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import tomlkit

from ._basemodel import BaseModel
from ._util import resolve_relative
from .appconfig import AppConfig, AppConfigData, AppConfigLocation
from .const import GIT_WS_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT
from .datamodel import GroupFilters, Project
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

    main_path: Path
    """
    Path to main project. Relative to workspace root directory.
    """

    @staticmethod
    def load(path: Path) -> "Info":
        """
        Load Workspace Information from GitWS root directory at `path`.

        The workspace information is stored at `{path}/.gitws/info.toml`.

        Args:
            path: Path to GitWS root directory.
        """
        infopath = path / INFO_PATH
        doc = tomlkit.parse(infopath.read_text())
        return Info(
            main_path=doc["main_path"],
        )

    def save(self, path: Path):
        """
        Save Workspace Information at GitWS root directory at `path`.

        The workspace information is stored at `{path}/.gitws/info.toml`.

        Args:
            path: Path to GitWS root directory.
        """
        infopath = path / INFO_PATH
        infopath.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc = tomlkit.parse(infopath.read_text())
        except FileNotFoundError:
            doc = tomlkit.document()
            doc.add(tomlkit.comment("Git Workspace System File. DO NOT EDIT."))
            doc.add(tomlkit.nl())
            doc.add("main_path", "")  # type: ignore
        doc["main_path"] = str(self.main_path)
        infopath.write_text(tomlkit.dumps(doc))


class Workspace:

    """
    Workspace.

    The workspace contains all git clones, but is *NOT* a git clone itself.
    A workspace refers to a main git clone, which defines the workspace content (i.e. dependencies).

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

        The workspace root directory contains a sub directory `.gitws`.
        This one is searched upwards the given `path`.
        """
        path = find_workspace(path=path)
        if path:
            return path
        raise UninitializedError()

    @staticmethod
    def from_path(path=None) -> "Workspace":
        """
        Create :any:`Workspace` for existing workspace at `path`.

        Keyword Args:
            path (Path): directory or file within the workspace. Current working directory by default.

        Raises:
            UninitializedError: If directory of file is not within a workspace.

        The workspace root directory contains a sub directory `.gitws`.
        This one is searched upwards the given `path`.
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
    def check_empty(path: Path, main_path: Path):
        """Check if Workspace at `path` with `main_path` is empty."""
        if any(item != main_path for item in path.iterdir()):
            raise WorkspaceNotEmptyError(resolve_relative(path))

    @staticmethod
    def init(
        path: Path,
        main_path: Path,
        manifest_path: Optional[Path] = None,
        group_filters: Optional[GroupFilters] = None,
        force: bool = False,
    ) -> "Workspace":
        """
        Initialize new :any:`Workspace` at `path`.

        Args:
            path:  Path to the workspace
            main_path:  Path to the main project. Relative to `path`.

        Keyword Args:
            manifest_path:  Path to the manifest file. Relative to `main_path`. Default is `git-ws.toml`.
            group_filters: Group Filters.
            force: Ignore that the workspace exists.

        Raises:
            OutsideWorkspaceError: `main_path` is not within `path`.
        """
        if not force:
            info = Workspace.is_init(path)
            if info:
                raise InitializedError(path, info.main_path)

        # Normalize
        try:
            main_path = (path / main_path).resolve().relative_to(path.resolve())
        except ValueError:
            raise OutsideWorkspaceError(path, main_path) from None

        # Initialize Info
        info = Info(main_path=main_path)
        info.save(path)
        workspace = Workspace(path.resolve(), info)
        with workspace.app_config.edit(AppConfigLocation.WORKSPACE) as config:
            config.manifest_path = str(manifest_path or MANIFEST_PATH_DEFAULT)
            config.group_filters = group_filters
        _LOGGER.info("Workspace path=%s main=%s", path, info.main_path)
        _LOGGER.info("%r", workspace.config)
        return workspace

    def deinit(self):
        """
        Deinitialize.

        Remove `GIT_WS_PATH` directory.
        """
        shutil.rmtree(self.path / GIT_WS_PATH)

    @property
    def main_path(self) -> Path:
        """Resolved Path to main project."""
        return self.path / self.info.main_path

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
        """Get Resolved Manifest Path."""
        return self.main_path / (manifest_path or self.app_config.options.manifest_path or MANIFEST_PATH_DEFAULT)

    def get_group_filters(self, group_filters: Optional[GroupFilters] = None) -> GroupFilters:
        """Get Group Selects."""
        if group_filters is None:
            return self.app_config.options.group_filters or GroupFilters()
        return group_filters

    def iter_obsoletes(self, used: List[Path]) -> Generator[Path, None, None]:
        """Yield obsolete paths except `used` ones."""
        usemap: Dict[str, Any] = {GIT_WS_PATH.name: {}}
        for path in used:
            pathmap = usemap
            for part in path.parts:
                pathmap[part] = {}
                pathmap = pathmap[part]
        yield from _iter_obsoletes(self.path, usemap)


def _iter_obsoletes(path, usemap):
    for sub in sorted(path.iterdir()):
        if sub.name in usemap:
            subusemap = usemap[sub.name]
            if subusemap:
                yield from _iter_obsoletes(sub, subusemap)
        elif sub.is_dir():
            yield sub
