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
Manifest Format.

We support multiple manifest formats. The :any:`AManifestFormat` class describes the access interface.
"""
from pathlib import Path
from typing import Optional

from .datamodel import ManifestSpec


class IncompatibleFormat(RuntimeError):
    """Incompatibility Error."""


class AManifestFormat:

    """
    Manifest Format.

    Specific Implementations of this class, handle specific manifest formats.
    """

    prio: int = 0

    def is_compatible(self, path: Path) -> bool:
        """Check If File At ``path`` Is Compatible."""
        # pylint: disable=unused-argument
        return False

    def load(self, path: Path) -> ManifestSpec:
        """
        Load Manifest From ``path``.

        Raises:
            ManifestNotFoundError: if file is not found
            IncompatibleFormat: Not Supported File Format.
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        raise IncompatibleFormat(path)

    def dump(self, spec: ManifestSpec, path: Optional[Path] = None) -> str:
        """
        Return :any:`ManifestSpec` As String.

        Args:
            spec: Manifest Spec

        Keyword Args:
            doc: Existing Document To Be Updated.
            path: Path To Possibly Existing Document.
        """
        raise IncompatibleFormat(path)

    def save(self, spec: ManifestSpec, path: Path, update: bool = True):
        """
        Save ``spec`` At ``path``.

        Keyword Args:
            update: Additional Attributes And Comments Added By The User Are **Kept**.
                    Otherwise The File Is Just Overwritten.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        if update:
            path.write_text(self.dump(spec, path=path))
        else:
            path.write_text(self.dump(spec))

    def upgrade(self, path: Path):
        """Upgrade :any:`ManifestSpec` at ``path`` To Latest Version Including Documentation."""
        raise IncompatibleFormat(path)
