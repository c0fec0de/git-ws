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
    cwdrel = resolve_relative(cwd) if cwd else None
    try:
        result = subprocess.run(cmd, capture_output=capture_output, check=check, cwd=cwd)
        _LOGGER.info("run(%r, cwd='%s') OK stdout=%r stderr=%r", cmd, cwdrel, result.stdout, result.stderr)
        return result
    except subprocess.CalledProcessError as error:
        _LOGGER.info("run(%r, cwd='%s') FAILED stdout=%r stderr=%r", cmd, cwdrel, error.stdout, error.stderr)
        raise error


def no_echo(text: str, **kwargs):
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


def get_repr(args=None, kwargs=None):
    """Return `repr()` string."""
    parts = list(args or [])
    for item in kwargs:
        try:
            name, value = item
            parts.append(f"{name}={value!r}")
        except ValueError:
            name, value, default = item
            if value != default:
                parts.append(f"{name}={value!r}")
    return ", ".join(parts)
