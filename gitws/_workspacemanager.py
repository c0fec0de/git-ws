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
Workspace Management.
"""
import hashlib
import shutil
from os import readlink
from pathlib import Path
from shutil import copy2
from typing import Any, Dict, Generator, List, Optional

from ._util import exception2logging, no_echo, relative
from .const import COLOR_ACTION, COLOR_BANNER, GIT_WS_PATH
from .datamodel import FileRefs, WorkspaceFileRef, WorkspaceFileRefs
from .exceptions import FileRefConflict, FileRefModifiedError, GitCloneNotCleanError, OutsideWorkspaceError
from .git import Git
from .workspace import Workspace

HASH_CHUNKSIZE = 65536
FileRefMap = Dict[Path, WorkspaceFileRef]


class WorkspaceManager:
    """
    Workspace Manager.

    A workspace contains git clones and copied/symlinked files from them.
    The :any:`WorkspaceManager` maintains copies or symlinks of files from git clones and helps to tidy up.

    It is not forbidden to link/copy a file from one git clone to another.
    """

    def __init__(self, workspace: Workspace, secho=None):
        self.workspace: Workspace = workspace
        self.secho = secho or no_echo
        assert workspace.path.is_absolute()
        self._knownpaths: List[Path] = []
        self._filerefmap: FileRefMap = {}

    def clear(self):
        """Clear."""
        self._knownpaths.clear()
        self._filerefmap.clear()

    def add(self, path: Optional[str], linkfiles: Optional[FileRefs] = None, copyfiles: Optional[FileRefs] = None):
        """
        Add project to be tracked.

        Args:
            path: Project Path relative to workspace root directory.
            linkfiles: symbolic links to be created.
            copyfiles: files to be copied.
        """
        if path:
            self._knownpaths.append(Path(path))
        project_path = path or "."
        self.__check_path((self.workspace.path / project_path).resolve(), "project")
        if linkfiles:
            for linkfile in linkfiles:
                fileref = WorkspaceFileRef(
                    type_="link",
                    project_path=project_path,
                    src=linkfile.src,
                    dest=linkfile.dest,
                )
                self._add_fileref(fileref)
        if copyfiles:
            for copyfile in copyfiles:
                fileref = WorkspaceFileRef(
                    type_="copy",
                    project_path=project_path,
                    src=copyfile.src,
                    dest=copyfile.dest,
                )
                self._add_fileref(fileref)

    def _add_fileref(self, fileref: WorkspaceFileRef):
        filerefmap = self._filerefmap
        dest = Path(fileref.dest)
        with exception2logging():
            if dest in filerefmap:
                workspace_path = self.workspace.path
                efileref = filerefmap[dest]
                # create nice relative paths in exception message
                destabs = workspace_path / fileref.dest
                existingabs = workspace_path / efileref.project_path / efileref.src
                conflictabs = workspace_path / fileref.project_path / fileref.src
                raise FileRefConflict(relative(destabs), relative(existingabs), relative(conflictabs))
            self._knownpaths.append(dest)
            filerefmap[dest] = fileref

    def is_outdated(self) -> bool:
        """Check if there is anything to do."""
        return bool(self._filerefmap.values())

    def update(self, force: bool = False) -> None:
        """Update File References."""
        with self.workspace.edit_info() as info:
            existing = info.filerefs
            self._rm_obsolete(existing, force)
            self._update(existing, force)

    def prune(self, force: bool = False):
        """Remove obsolete stuff."""
        for obsolete_path in self._iter_obsoletes():
            rel_path = relative(obsolete_path)
            self.secho(f"===== {rel_path} (OBSOLETE) =====", fg=COLOR_BANNER)
            self.secho(f"Removing {str(rel_path)!r}.", fg=COLOR_ACTION)
            git = Git(obsolete_path, secho=self.secho)
            if force or not git.is_cloned() or git.is_empty():
                shutil.rmtree(obsolete_path, ignore_errors=True)
            else:
                raise GitCloneNotCleanError(relative(rel_path))

    def _rm_obsolete(self, existing: WorkspaceFileRefs, force: bool):
        filerefmap = self._filerefmap

        for efileref in tuple(existing):
            dest = Path(efileref.dest)
            if dest not in filerefmap:
                with exception2logging("Cannot remove: "):
                    self.__remove_fileref(efileref, force)

                    # update tracker
                    existing.remove(efileref)

    def _update(self, existing: WorkspaceFileRefs, force: bool):
        workspace_path = self.workspace.path
        efilerefmap: FileRefMap = {Path(fileref.dest): fileref for fileref in existing}

        for dest, fileref in self._filerefmap.items():
            with exception2logging("Cannot update: "):
                # calculate source hash on copied file
                if fileref.type_ == "copy":
                    srcabs = workspace_path / fileref.project_path / fileref.src
                    self.__check_path(srcabs, "source", exists=True, is_file=True)
                    hash_ = _get_filehash(srcabs)
                    fileref = fileref.model_copy(update={"hash_": hash_})  # noqa: PLW2901

                # existing file up-to-date?
                efileref = efilerefmap.get(dest)
                if efileref != fileref:
                    # remove
                    if efileref:
                        self.__remove_fileref(efileref, force)
                        existing.remove(efileref)

                    # create
                    self.__create_fileref(fileref, force)
                    existing.append(fileref)
                else:
                    # update tracker (Move to the end, otherwise behaviour depends on update history)
                    existing.remove(fileref)
                    existing.append(fileref)

    def __remove_fileref(self, fileref: WorkspaceFileRef, force: bool):
        """Remove existing `fileref`."""
        workspace_path = self.workspace.path
        destabs = workspace_path / fileref.dest
        self.__check_path(destabs, "destination", is_file=True)

        if destabs.exists():
            # Check for Modifications
            if not force:
                if fileref.hash_:
                    desthash = _get_filehash(destabs)
                    if desthash != fileref.hash_:
                        # create nice relative paths in exception message
                        srcabs = workspace_path / fileref.project_path / fileref.src
                        raise FileRefModifiedError(relative(destabs), relative(srcabs))
                if fileref.type_ == "link" and destabs.is_symlink():
                    srcabs = workspace_path / fileref.project_path / fileref.src
                    esrcabs = Path(readlink(destabs))
                    if srcabs != esrcabs:
                        raise FileRefModifiedError(relative(destabs), relative(srcabs))

            # Remove
            self.secho(f"Removing '{relative(destabs)!s}'")
            destabs.unlink()

    def __create_fileref(self, fileref: WorkspaceFileRef, force):
        """Create `fileref`."""
        workspace_path = self.workspace.path
        destabs = workspace_path / fileref.dest
        self.__check_path(destabs, "destination", exists=None if force else False, is_file=True)
        srcabs = workspace_path / fileref.project_path / fileref.src
        self.__check_path(srcabs, "source", exists=True, is_file=True)

        # Ensure parent folder exists
        destabs.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing file
        if force and destabs.exists():
            destabs.unlink()

        filereftype = fileref.type_
        if filereftype == "copy":
            self.secho(f"Copying '{relative(srcabs)!s}' -> '{relative(destabs)!s}'")
            copy2(srcabs, destabs)
        elif filereftype == "link":
            self.secho(f"Linking '{relative(srcabs)!s}' -> '{relative(destabs)!s}'")
            destabs.symlink_to(srcabs)
        else:
            raise RuntimeError(f"Unknown filereftype {filereftype!r}")  # pragma: no cover

    def __check_path(self, path, what, exists=None, is_file=None):
        assert path.is_absolute()
        try:
            path.relative_to(self.workspace.path)
        except ValueError:
            raise OutsideWorkspaceError(self.workspace.path, path, what) from None
        path_exists = path.exists()
        if exists is True:
            if not path_exists:
                raise FileNotFoundError(f"{what} file {str(relative(path))!r} does not exists!")
        elif exists is False:
            if path_exists:
                raise RuntimeError(f"{what} file {str(relative(path))!r} already exists!")
        if path_exists:
            if is_file is True and not path.is_file():
                raise RuntimeError(f"{what} file {str(relative(path))!r} is not a file!")
            if is_file is False and path.is_file():
                raise RuntimeError(f"{what} file {str(relative(path))!r} is a file!")  # pragma: no cover

    def _iter_obsoletes(self) -> Generator[Path, None, None]:
        """Yield paths except *used* ones."""
        usemap: Dict[str, Any] = {GIT_WS_PATH.name: {}}
        for path in self._knownpaths:
            pathmap = usemap
            for part in path.parts:
                pathmap[part] = {}
                pathmap = pathmap[part]
        yield from self.__iter_obsoletes(self.workspace.path, usemap)

    def __iter_obsoletes(self, path, usemap):
        for sub in sorted(path.iterdir()):
            if sub.name in usemap:
                subusemap = usemap[sub.name]
                if subusemap:
                    yield from self.__iter_obsoletes(sub, subusemap)
            elif sub.is_dir():
                yield sub


def _get_filehash(path: Path):
    hash_ = hashlib.sha512()

    with open(path, "rb") as file:
        while True:
            data = file.read(HASH_CHUNKSIZE)
            if not data:
                break
            hash_.update(data)
    return int(hash_.hexdigest(), 16)
