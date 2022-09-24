"""Workspace."""
import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from ._util import resolve_relative
from .const import ANYREPO_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT
from .exceptions import InitializedError, OutsideWorkspaceError, UninitializedError

_LOGGER = logging.getLogger(__name__)


class Info(BaseModel):
    """
    Workspace Information Container.

    The workspace information container assembles all information which has to be kept persistant between tool
    invocations.

    :param main_path (Path): Path to main project. Relative to workspace root directory.
    :param mainfest_path (Path): Path to manifest file. Relative to `main_path`.
    """

    main_path: Path
    manifest_path: Path = MANIFEST_PATH_DEFAULT

    @staticmethod
    def load(path: Path) -> "Info":
        """Load Workspace Information from AnyRepo root directory `path`."""
        infopath = path / INFO_PATH
        data = yaml.load(infopath.read_text(), Loader=yaml.Loader)
        return Info(**data)  # type: ignore

    def save(self, path: Path):
        """Save Workspace Information at AnyRepo root directory `path`."""
        infopath = path / INFO_PATH
        infopath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "main_path": str(self.main_path),
            "manifest_path": str(self.manifest_path),
        }
        infopath.write_text(yaml.dump(data))


class Workspace:

    """
    Workspace.

    The workspace contains all git clones, but is *NOT* a git clone itself.
    A workspace refers to a main git clone, which defines the workspace content (i.e. dependencies).

    :param path (Path): Workspace Root Directory.
    :param info (Info): Workspace Information.
    """

    def __init__(self, path: Path, info: Info):
        super().__init__()
        self.path = path
        self.info = info

    @staticmethod
    def find_path(path: Optional[Path] = None):
        """Find workspace root directory."""
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
        Create :any:`Workspace`.

        :param path:  Path within the workspace (Default is the current working directory).
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

        :param path (Path):  Path to the workspace
        :param main_path (Path):  Path to the main project.
        :param manifest_path (Path):  Path to the manifest file.
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
