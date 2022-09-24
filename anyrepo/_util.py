"""Utilities."""
import logging
import subprocess
from pathlib import Path
from typing import Optional

_LOGGER = logging.getLogger("anyrepo")
# Dependencies to any anyrepo module are forbidden here!

_LOGLEVELMAP = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def get_loglevel(verbose: int):
    """Return `logging.level` according to verbosity."""
    return _LOGLEVELMAP.get(verbose, logging.DEBUG)


def run(cmd, cwd=None, capture_output=False, check=True):
    """Simplified wrapper around :any:`subprocess.run`."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, check=check, cwd=cwd)
        _LOGGER.info("run(%r) OK stdout=%r stderr=%r", cmd, result.stdout, result.stderr)
        return result
    except subprocess.CalledProcessError as error:
        _LOGGER.info("run(%r) FAILED stdout=%r stderr=%r", cmd, error.stdout, error.stderr)
        raise error


def no_banner(text: str):
    """Just suppress `text`."""


def resolve_relative(path: Path, base: Optional[Path] = None):
    """
    Return resolved `path` relative to `base`.

    :param path (Path): Path
    :param base (Path): Base Path. Current Working Directory by default.
    """
    if not base:
        base = Path.cwd()
    path = base / path
    path = path.resolve()
    try:
        return path.relative_to(base)
    except ValueError:
        return path.resolve()


def path_upwards(path: Path, sub: Path) -> Path:
    """Return `path` without `sub`."""
    pathparts = path.parts
    for part in reversed(sub.parts):
        if part == pathparts[-1]:
            pathparts = pathparts[:-1]
        else:
            raise ValueError(f"{sub} is not within {path}")
    return Path(*pathparts)
