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

"""Workspace Finder."""
from pathlib import Path
from typing import Optional

from .const import INFO_PATH


def find_workspace(path: Optional[Path] = None) -> Optional[Path]:
    """
    Find Workspace Root Directory.

    Keyword Args:
        path (Path): directory or file within the workspace. Current working directory by default.

    The workspace root directory contains a sub directory `.gitws`.
    This one is searched upwards the given `path`.
    """
    spath = path or Path.cwd()
    while True:
        gitwspath = spath / INFO_PATH
        if gitwspath.exists():
            return spath
        if spath == spath.parent:
            break
        spath = spath.parent
    return None
