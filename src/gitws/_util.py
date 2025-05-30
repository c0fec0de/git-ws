# Copyright 2022-2025 c0fec0de
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

"""Utilities."""

import logging
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import tomlkit

LOGGER = logging.getLogger("git-ws")
# Dependencies to any gitws module are forbidden here!


def run(cmd, cwd=None, capture_output=False, check=True, secho=None):
    """Simplified wrapper around :any:`subprocess.run`."""
    cwdrelstr = str(resolve_relative(cwd)) if cwd else None
    # format errors in red
    stderr = None if capture_output or not secho else subprocess.PIPE
    try:
        result = subprocess.run(cmd, capture_output=capture_output, stderr=stderr, check=check, cwd=cwd)  # noqa: S603
        LOGGER.debug("run(%r, cwd=%r) OK stdout=%r stderr=%r", cmd, cwdrelstr, result.stdout, result.stderr)
        if stderr and result.stderr:
            secho(result.stderr.decode("utf-8").rstrip())
        return result
    except subprocess.CalledProcessError as error:
        LOGGER.debug("run(%r, cwd=%r) FAILED stdout=%r stderr=%r", cmd, cwdrelstr, error.stdout, error.stderr)
        if stderr and error.stderr:
            secho(error.stderr.decode("utf-8").rstrip(), fg="red", err=True)
        raise error


def no_echo(text: str, err=False, **kwargs):
    """Just suppress ``text``."""
    if err:
        print(text, file=sys.stderr)


def resolve_relative(path: Path, base: Optional[Path] = None) -> Path:
    """
    Return resolved ``path`` relative to ``base``.

    Args:
        path: Path

    Keyword Args:
        base: Base Path. Current Working Directory by default.
    """
    base = (base or Path.cwd()).resolve()
    path = (base / path).resolve()
    return relative(path, base)


def relative(path: Path, base: Optional[Path] = None) -> Path:
    """
    Return ``path`` relative to ``base``.

    Args:
        path: Path

    Keyword Args:
        base: Base Path. Current Working Directory by default.
    """
    base = base or Path.cwd()
    try:
        return path.relative_to(base)
    except ValueError:
        # Try to determine a relative path, which is save
        relpath = Path(os.path.relpath(path, start=base))
        abspath = (base / relpath).resolve()
        if path == abspath:
            return relpath
        return path


def get_repr(obj=None, args=None, kwargs=None):
    """Return `repr()` string."""
    parts = [f"{arg!r}" for arg in args or []]
    for item in kwargs or []:
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


def as_dict(obj, exclude_defaults: bool = True):
    """Transform to dictionary."""
    return obj.model_dump(by_alias=True, exclude_none=True, exclude_defaults=exclude_defaults)


@contextmanager
def exception2logging(info: Optional[str] = ""):
    """Capture Exception and Report as Error to logging."""
    try:
        yield
    except Exception as exc:
        LOGGER.error("%s%s", info, exc)
