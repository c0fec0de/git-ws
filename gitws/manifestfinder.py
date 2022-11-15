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

"""Find proper manifest."""

from pathlib import Path
from typing import Optional

from .const import MANIFESTS_PATH
from .git import Git


def find_manifest(path: Path) -> Optional[Path]:
    """Return Path to manifest if clone has been tagged before."""
    if path.exists():
        git = Git(path=path)
        if not git.get_branch():
            tag = git.get_tag()
            if tag:
                manifest_path = MANIFESTS_PATH / f"{tag}.toml"
                if (path / manifest_path).exists():
                    return manifest_path
    return None
