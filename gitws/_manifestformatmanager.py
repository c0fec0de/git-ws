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
Manifest Format Manager.
"""
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from pydantic import ConfigDict, PrivateAttr

from ._basemodel import BaseModel
from .datamodel import ManifestSpec
from .manifestformat import AManifestFormat, IncompatibleFormat

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


class Handler(BaseModel):

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    path: Path
    fmt: AManifestFormat

    def load(self) -> ManifestSpec:
        """
        Load Manifest.

        Raises:
            ManifestNotFoundError: if file is not found
            IncompatibleFormat: Not Supported File Format.
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        return self.fmt.load(self.path)

    def save(self, spec: ManifestSpec, update: bool = True):
        """
        Save ``spec``.

        Keyword Args:
            update: Additional Attributes And Comments Added By The User Are **Kept**.
                    Otherwise The File Is Just Overwritten.
        """
        self.fmt.save(spec, self.path, update=update)


class ManifestFormatManager(BaseModel):

    """
    Manifest Format Manager.
    """

    _manifestformats: List[AManifestFormat] = PrivateAttr(default_factory=list)

    @staticmethod
    def from_env() -> "ManifestFormatManager":
        """Create :any:`ManifestFormatManager` With All Loaded Plugins."""
        mngr = ManifestFormatManager()
        mngr.load_plugins()
        return mngr

    def add(self, manifestformat: AManifestFormat):
        """Register Manifest Format."""
        self._manifestformats.append(manifestformat)

    @property
    def formats(self) -> Tuple[AManifestFormat, ...]:
        """Formats."""
        return tuple(self._manifestformats)

    def load_plugins(self):
        """
        Load Manifest Format Plugins.
        """
        for entry_point in entry_points(group="gitws.manifestformat"):
            cls = entry_point.load()
            assert issubclass(cls, AManifestFormat), cls
            self.add(cls())

    # TODO: is there a better name than 'handle'?

    @contextmanager
    def handle(self, path: Path) -> Iterator[Handler]:
        """Return Context With :any:`AManifestFormat`."""
        fmt: Optional[AManifestFormat] = None
        for manifestformat in self._manifestformats:
            if not manifestformat.is_compatible(path):
                continue
            if not fmt or manifestformat.prio > fmt.prio:
                fmt = manifestformat
        if not fmt:
            raise IncompatibleFormat(path)
        yield Handler(path=path, fmt=fmt)

    def load(self, path: Path) -> ManifestSpec:
        """
        Load Manifest From ``path``.

        Raises:
            ManifestNotFoundError: if file is not found
            IncompatibleFormat: Not Supported File Format.
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        with self.handle(path) as fmt:
            return fmt.load()

    def save(self, spec: ManifestSpec, path: Path, update: bool = True):
        """
        Save ``spec`` At ``path``.

        Keyword Args:
            update: Additional Attributes And Comments Added By The User Are **Kept**.
                    Otherwise The File Is Just Overwritten.
        """
        with self.handle(path) as fmt:
            fmt.save(spec, update=update)
