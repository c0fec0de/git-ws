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
Manifest format_ Manager.
"""
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from pydantic import ConfigDict, PrivateAttr

from ._basemodel import BaseModel
from .datamodel import ManifestSpec
from .exceptions import IncompatibleFormatError
from .manifestformat import ManifestFormat

if sys.version_info < (3, 10):  # pragma: no cover
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


class Handler(BaseModel):
    """format_ Handler."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    path: Path
    format_: ManifestFormat

    def load(self) -> ManifestSpec:
        """
        Load Manifest.

        Raises:
            ManifestNotFoundError: if file is not found
            IncompatibleFormatError: Not Supported File format_.
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        return self.format_.load(self.path)

    def save(self, spec: ManifestSpec, update: bool = True):
        """
        Save ``spec``.

        Args:
            spec: Manifest specification to be stored.

        Keyword Args:
            update: Additional Attributes And Comments Added By The User Are **Kept**.
                    Otherwise The File Is Just Overwritten.
        """
        self.format_.save(spec, self.path, update=update)


class ManifestFormatManager(BaseModel):
    """
    Manifest format_ Manager.
    """

    _manifest_formats: List[ManifestFormat] = PrivateAttr(default_factory=list)

    def add(self, manifestformat: ManifestFormat):
        """Register Manifest format_."""
        self._manifest_formats.append(manifestformat)

    @property
    def manifest_formats(self) -> Tuple[ManifestFormat, ...]:
        """Formats."""
        return tuple(self._manifest_formats)

    def load_plugins(self):
        """
        Load Manifest format_ Plugins.
        """
        for entry_point in entry_points(group="gitws.manifestformat"):
            cls = entry_point.load()
            assert issubclass(cls, ManifestFormat), cls
            self.add(cls())

    @contextmanager
    def handle(self, path: Path) -> Iterator[Handler]:
        """Return Context With :any:`ManifestFormat`."""
        format_: Optional[ManifestFormat] = None
        for manifestformat in self._manifest_formats:
            if not manifestformat.is_compatible(path):
                continue
            if not format_ or manifestformat.prio > format_.prio:
                format_ = manifestformat
        if not format_:
            raise IncompatibleFormatError(path)
        yield Handler(path=path, format_=format_)

    def load(self, path: Path) -> ManifestSpec:
        """
        Load Manifest From ``path``.

        Raises:
            ManifestNotFoundError: if file is not found
            IncompatibleFormatError: Not Supported File format_.
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        with self.handle(path) as fmt:
            return fmt.load()


_MANAGER: Optional[ManifestFormatManager] = None


def get_manifest_format_manager() -> ManifestFormatManager:
    """
    Get Global Manifest Format Manager.

    The manifest format manager supports a plugin mechanism.
    Plugin loading takes time.
    This method returns a cached global manifest format manager instance.
    """
    global _MANAGER  # noqa: PLW0603
    if not _MANAGER:
        _MANAGER = ManifestFormatManager()
        _MANAGER.load_plugins()

    return _MANAGER
