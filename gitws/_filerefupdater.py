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
File Reference Updater.

File can be referend to be linked (:any:`LinkFileUpdater`) or copied (:any:`CopyFileUpdater`). 
"""
import logging
from filecmp import cmp
from pathlib import Path
from shutil import copy2

from ._util import no_echo, relative
from .datamodel import FileRef, FileRefs, FileRefsMutable, ProjectFileRefs, ProjectFileRefsMutable
from .exceptions import OutsideWorkspaceError

_LOGGER = logging.getLogger("git-ws")


class AFileRefUpdater:

    """Abstract File Reference Updater."""

    what: str = ""

    def __init__(self, path: Path, secho=None):
        self.path: Path = path
        self._project_filerefs: ProjectFileRefs = {}
        self.secho = secho or no_echo
        assert path.is_absolute()

    def set(self, path: str, filerefs: FileRefs):
        """Set `filerefs` for `path`."""
        if filerefs:
            self._project_filerefs[path] = filerefs
        else:
            self._project_filerefs.pop(path, None)

    def get(self, path: str) -> FileRefs:
        """Get `filerefs` for `path`"""
        filerefs: FileRefs = self._project_filerefs.get(path, [])  # type: ignore
        return filerefs

    def __bool__(self) -> bool:
        return bool(self._project_filerefs)

    def remove(self, existing: ProjectFileRefsMutable):
        """Remove obsolete file references and update tracking in `existing`."""
        for path, efilerefs in tuple(existing.items()):
            required = self.get(path)
            if required:
                # remove some
                for efileref in tuple(efilerefs):
                    if efileref not in required:
                        self._remove_fileref(efilerefs, efileref)
            else:
                # remove all
                for efileref in tuple(efilerefs):
                    self._remove_fileref(efilerefs, efileref)

            # remove empty list
            if not efilerefs:
                existing.pop(path)

    def _remove_fileref(self, efilerefs: FileRefsMutable, fileref: FileRef):
        dest = self.path / fileref.dest
        try:
            self.__check_path(dest, "destination")
            self._remove(dest)
            efilerefs.remove(fileref)
        except Exception as exc:  # pylint: disable=broad-exception-caught # pragma: no cover
            _LOGGER.error("Cannot remove %s: %s", self.what, exc)

    def _remove(self, dest: Path):
        try:
            destrel = relative(dest)
            self.secho(f"Removing '{destrel!s}'")
            dest.unlink()
        except FileNotFoundError:
            pass

    def update(self, existing: ProjectFileRefsMutable):
        """Update file references and update tracking in `existing`."""
        for path, filerefs in self._project_filerefs.items():
            efilerefs = existing.setdefault(path, [])
            for fileref in filerefs:
                try:
                    self._update_fileref(efilerefs, path, fileref)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    _LOGGER.error("Cannot update %s: %s", self.what, exc)

    def _update_fileref(self, efilerefs: FileRefsMutable, path: str, fileref: FileRef):
        dest = (self.path / fileref.dest).resolve()
        src = (self.path / path / fileref.src).resolve()
        self.__check_path(dest, "destination")
        self.__check_path(src, "source")
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._update(src, dest)
        if fileref not in efilerefs:
            efilerefs.append(fileref)

    def _update(self, src: Path, dest: Path):
        raise NotImplementedError()

    def __check_path(self, path, what):
        try:
            path.relative_to(self.path)
        except ValueError:
            raise OutsideWorkspaceError(self.path, path, what) from None


class LinkFileUpdater(AFileRefUpdater):

    """Symbolic Link Updater."""

    what: str = "symbolic link"

    def _update(self, src: Path, dest: Path):
        if not dest.exists():
            srcrel = relative(src)
            destrel = relative(dest)
            if not src.exists():
                _LOGGER.warning("Link source '%s' does not exists!", srcrel)
            else:
                self.secho(f"Linking '{srcrel!s}' -> '{destrel!s}'")
                dest.symlink_to(src)


class CopyFileUpdater(AFileRefUpdater):

    """Copy File Updater."""

    what: str = "copied file"

    def _update(self, src: Path, dest: Path):
        srcrel = relative(src)
        if not src.exists():
            _LOGGER.warning("Copy source '%s' does not exists!", srcrel)
        elif not dest.exists() or not cmp(src, dest):
            destrel = relative(dest)
            self.secho(f"Copying '{srcrel!s}' -> '{destrel!s}'")
            copy2(src, dest)
