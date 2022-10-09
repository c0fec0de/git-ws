"""Utilities."""
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

import tomlkit

_LOGGER = logging.getLogger("anyrepo")
# Dependencies to any anyrepo module are forbidden here!


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
        # Try to determine a relative path, which is save
        abspath = path.resolve()
        relpath = Path(os.path.relpath(path, start=base))
        resolvedpath = (base / relpath).resolve()
        if abspath == (resolvedpath):
            return relpath
        return abspath


def get_repr(obj=None, args=None, kwargs=None):
    """Return `repr()` string."""
    parts = []
    for arg in args or []:
        parts.append(f"{arg!r}")
    for item in kwargs or []:
        try:
            name, value = item
            parts.append(f"{name}={value!r}")
        except ValueError:
            name, value, default = item
            if value != default:
                parts.append(f"{name}={value!r}")
    joined = ", ".join(parts)
    if obj:
        return f"{obj.__class__.__qualname__}({joined})"
    return joined


def removesuffix(text, suffix):
    """
    Remove Suffix identical to function available since python 3.9.

    >>> removesuffix('my text', 'xt')
    'my te'
    >>> removesuffix('my text', 'other')
    'my text'
    """
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text


def add_info(doc: tomlkit.TOMLDocument, text):
    """Add Multi-Line Documentation to TOML document."""
    for line in text.split("\n"):
        comment = f"## {line}" if line else "##"
        doc.add(tomlkit.items.Comment(tomlkit.items.Trivia(comment_ws="  ", comment=comment)))


def add_comment(doc: tomlkit.TOMLDocument, text):
    """Add Multi-Line Comment to TOML document."""
    for line in text.split("\n"):
        comment = f"# {line}" if line else "#"
        doc.add(tomlkit.items.Comment(tomlkit.items.Trivia(comment_ws="  ", comment=comment)))


def as_dict(obj):
    """Transform to dictionary."""
    return obj.dict(by_alias=True, exclude_none=True, exclude_defaults=True)
