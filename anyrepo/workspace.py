"""
Workspace Handling.

The :any:`Workspace` class represents the file system location containing all git clones.
:any:`Info` is a helper.
"""
import logging
from pathlib import Path
from typing import Optional

import tomlkit

from ._basemodel import BaseModel
from ._util import resolve_relative
from .const import ANYREPO_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT
from .exceptions import InitializedError, OutsideWorkspaceError, UninitializedError

_LOGGER = logging.getLogger("anyrepo")


class Info(BaseModel):
    """
    Workspace Information Container.

    The workspace information container assembles all information which has to be kept persistant between tool
    invocations.

    Keyword Args:
        main_path (Path): Path to main project. Relative to workspace root directory.
        mainfest_path (Path): Path to manifest file. Relative to `main_path`.
    """

    main_path: Path
    manifest_path: Path = MANIFEST_PATH_DEFAULT

    @staticmethod
    def load(path: Path) -> "Info":
        """
        Load Workspace Information from AnyRepo root directory at `path`.

        The workspace information is stored at `{path}/.anyrepo/info.yaml`.

        Args:
            path (Path): Path to AnyRepo root directory.
        """
        infopath = path / INFO_PATH
        doc = tomlkit.parse(infopath.read_text())
        return Info(
            main_path=doc["main_path"],
            manifest_path=doc["manifest_path"],
        )

    def save(self, path: Path):
        """
        Save Workspace Information at AnyRepo root directory at `path`.

        The workspace information is stored at `{path}/.anyrepo/info.yaml`.

        Args:
            path (Path): Path to AnyRepo root directory.
        """
        infopath = path / INFO_PATH
        infopath.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc = tomlkit.parse(infopath.read_text())
        except FileNotFoundError:
            doc = tomlkit.document()
            doc.add(tomlkit.comment("AnyRepo System File. DO NOT EDIT."))
            doc.add(tomlkit.nl())
            doc.add("main_path", "")  # type: ignore
            doc.add("manifest_path", "")  # type: ignore
        doc["main_path"] = str(self.main_path)
        doc["manifest_path"] = str(self.manifest_path)
        infopath.write_text(tomlkit.dumps(doc))


class Workspace:

    """
    Workspace.

    The workspace contains all git clones, but is *NOT* a git clone itself.
    A workspace refers to a main git clone, which defines the workspace content (i.e. dependencies).

    Args:
        path (Path): Workspace Root Directory.
        info (Info): Workspace Information.
    """

    def __init__(self, path: Path, info: Info):
        super().__init__()
        self.path = path
        self.info = info

    def __eq__(self, other):
        if isinstance(other, Workspace):
            return (self.path, self.info) == (other.path, other.info)
        return NotImplemented

    @staticmethod
    def find_path(path: Optional[Path] = None):
        """
        Find Workspace Root Directory.

        Keyword Args:
            path (Path): directory or file within the workspace. Current working directory be default.

        Raises:
            UninitializedError: If directory of file is not within a workspace.

        The workspace root directory contains a sub directory `.anyrepo`.
        This one is searched upwards the given `path`.
        """
        spath = path or Path.cwd()
        while True:
            anyrepopath = spath / ANYREPO_PATH
            if anyrepopath.exists():
                return spath
            if spath == spath.parent:
                break
            spath = spath.parent
        raise UninitializedError()

    @staticmethod
    def from_path(path=None) -> "Workspace":
        """
        Create :any:`Workspace` for existing workspace at `path`.

        Keyword Args:
            path (Path): directory or file within the workspace. Current working directory be default.

        Raises:
            UninitializedError: If directory of file is not within a workspace.

        The workspace root directory contains a sub directory `.anyrepo`.
        This one is searched upwards the given `path`.
        """
        path = Workspace.find_path(path=path)
        _LOGGER.info("path=%s", path)
        info = Info.load(path)
        _LOGGER.info("Loaded %s %s %s", path, info.main_path, info.manifest_path)
        return Workspace(path, info)

    @staticmethod
    def init(path: Path, main_path: Path, manifest_path: Path = MANIFEST_PATH_DEFAULT) -> "Workspace":
        """
        Initialize new :any:`Workspace` at `path`.

        Args:
            path (Path):  Path to the workspace
            main_path (Path):  Path to the main project.

        Keyword Args:
            manifest_path (Path):  Path to the manifest file.

        Raises:
            OutsideWorkspaceError: `main_path` is not within `path`.
        """
        infopath = path / INFO_PATH
        if infopath.exists():
            raise InitializedError(path)

        # Normalize
        main_path = main_path.resolve()
        manifest_path = resolve_relative(main_path / manifest_path, base=main_path)
        try:
            main_path = main_path.relative_to(path)
        except ValueError:
            raise OutsideWorkspaceError(path, main_path) from None

        # Initialize Info
        info = Info(main_path=main_path, manifest_path=manifest_path)
        info.save(path)
        _LOGGER.info("Initialized %s %s %s", path, info.main_path, info.manifest_path)
        return Workspace(path, info)

    @property
    def main_path(self) -> Path:
        """Path to main project."""
        return self.path / self.info.main_path
