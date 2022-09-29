"""
Workspace Handling.

The :any:`Workspace` class represents the file system location containing all git clones.
:any:`Info` is a helper.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import tomlkit

from ._basemodel import BaseModel
from ._util import resolve_relative
from .const import ANYREPO_PATH, INFO_PATH, MANIFEST_PATH_DEFAULT
from .datamodel import Project
from .exceptions import InitializedError, OutsideWorkspaceError, UninitializedError
from .types import Groups

_LOGGER = logging.getLogger("anyrepo")


class Info(BaseModel):
    """
    Workspace Information Container.

    The workspace information container assembles all information which has to be kept persistant between tool
    invocations.

    Keyword Args:
        main_path: Path to main project. Relative to workspace root directory.
        mainfest_path: Path to manifest file. Relative to `main_path`.
        groups: Group Filtering.
    """

    main_path: Path
    manifest_path: Path = MANIFEST_PATH_DEFAULT
    groups: Optional[str] = None

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
        groups = doc.get("groups", None) or None  # legacy support
        return Info(
            main_path=doc["main_path"],
            manifest_path=doc["manifest_path"],
            groups=groups,
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
            doc.add("groups", "")  # type: ignore
        doc["main_path"] = str(self.main_path)
        doc["manifest_path"] = str(self.manifest_path)
        doc["groups"] = self.groups or ""
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
        _LOGGER.info("Loaded %s %r", path, info)
        return Workspace(path, info)

    @staticmethod
    def init(
        path: Path, main_path: Path, manifest_path: Path = MANIFEST_PATH_DEFAULT, groups: Groups = None
    ) -> "Workspace":
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
        info = Info(main_path=main_path, manifest_path=manifest_path, groups=groups)
        info.save(path)
        _LOGGER.info("Initialized %s %r", path, info)
        return Workspace(path, info)

    @property
    def main_path(self) -> Path:
        """Path to main project."""
        return self.path / self.info.main_path

    def get_project_path(self, project: Project, relative: bool = False) -> Path:
        """Project Path."""
        project_path = self.path / project.path
        if relative:
            project_path = resolve_relative(project_path)
        return project_path

    def get_manifest_path(self, manifest_path: Optional[Path] = None) -> Path:
        """Manifest Path."""
        return self.main_path / (manifest_path or self.info.manifest_path)

    def get_groups(self, groups: Groups = None) -> Groups:
        """Group Filter."""
        if groups is None:
            return self.info.groups
        return groups

    def iter_obsoletes(self, used: List[Path]) -> Generator[Path, None, None]:
        """Remove everything except `used`."""
        usemap: Dict[str, Any] = {ANYREPO_PATH.name: {}}
        for path in used:
            pathmap = usemap
            for part in path.parts:
                pathmap[part] = {}
                pathmap = pathmap[part]
        yield from _iter_obsoletes(self.path, usemap)


def _iter_obsoletes(path, usemap):
    for sub in path.iterdir():
        if sub.name in usemap:
            subusemap = usemap[sub.name]
            if subusemap:
                yield from _iter_obsoletes(sub, subusemap)
        elif sub.is_dir():
            yield sub
