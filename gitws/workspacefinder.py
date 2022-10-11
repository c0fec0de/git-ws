"""Workspace Finder."""
from pathlib import Path
from typing import Optional

from .const import GIT_WS_PATH


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
        gitwspath = spath / GIT_WS_PATH
        if gitwspath.exists():
            return spath
        if spath == spath.parent:
            break
        spath = spath.parent
    return None
