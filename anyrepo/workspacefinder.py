"""Workspace Finder."""
from pathlib import Path
from typing import Optional

from .const import ANYREPO_PATH


def find_workspace(path: Optional[Path] = None) -> Optional[Path]:
    """
    Find Workspace Root Directory.

    Keyword Args:
        path (Path): directory or file within the workspace. Current working directory by default.

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
    return None
