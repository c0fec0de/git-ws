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

"""Git Utilities."""

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from ._basemodel import BaseModel
from ._util import get_repr, run
from .exceptions import NoGitError

_RE_STATUS = re.compile(r"\A(?P<index>.)(?P<work>.)\s((?P<orig_path>.+) -> )?(?P<path>.+)\Z")
_LOGGER = logging.getLogger("git-ws")


class State(Enum):
    """
    Actual State

    >>> State(" ")
    <State.UNMODIFIED: ' '>
    >>> State("A")
    <State.ADDED: 'A'>
    """

    UNTRACKED = "?"
    IGNORED = "!"
    UNMODIFIED = " "
    MODIFIED = "M"
    TYPE_CHANGED = "T"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UPDATED_UNMERGED = "U"

    def __str__(self):
        return self.value


class Status(BaseModel):
    """Status."""

    def with_path(self, path: Path) -> "Status":
        """Return :any:`Status` with `path`."""
        raise NotImplementedError()

    def has_index_changes(self) -> bool:
        """Has Index Changes."""
        raise NotImplementedError()


class FileStatus(Status):

    """
    Git File Status Line.

    >>> status = FileStatus.from_str("?? file.txt")
    >>> status
    FileStatus(index=<State.UNTRACKED: '?'>, work=<State.UNTRACKED: '?'>, path=PosixPath('file.txt'))
    >>> str(status)
    '?? file.txt'
    >>> str(status.with_path(Path("base")))
    '?? base/file.txt'

    >>> status = FileStatus.from_str("R  src -> dest")
    >>> status
    FileStatus(index=<State.RENAMED: 'R'>, work=<State.UNMODIFIED: ' '>, path=PosixPath('dest'), orig_path=...
    >>> str(status)
    'R  src -> dest'
    >>> str(status.with_path(Path("base")))
    'R  base/src -> base/dest'
    """

    index: State
    """Status of the Index."""

    work: State
    """Status of Workiing Tree."""

    path: Path
    """File Path."""

    orig_path: Optional[Path] = None
    """File Path of the original file in case of a move."""

    def __str__(self):
        if self.orig_path:
            return f"{self.index}{self.work} {self.orig_path!s} -> {self.path!s}"
        return f"{self.index}{self.work} {self.path!s}"

    @staticmethod
    def from_str(line) -> "FileStatus":
        """Create v1 porcelain output."""
        mat = _RE_STATUS.match(line)
        assert mat, f"Invalid pattern {line}"
        return FileStatus(**mat.groupdict())

    def with_path(self, path: Path) -> "FileStatus":
        """Return :any:`FileStatus` with `path`."""
        if self.orig_path:
            return self.update(path=path / self.path, orig_path=path / self.orig_path)
        return self.update(path=path / self.path)

    def has_index_changes(self) -> bool:
        """Has Index Changes."""
        return self.index not in (State.UNMODIFIED, State.IGNORED, State.UNTRACKED)


class BranchStatus(Status):

    """Branch Status."""

    info: str
    """Info."""

    def __str__(self):
        return self.info

    @staticmethod
    def from_str(line) -> "BranchStatus":
        """Create v1 porcelain output."""
        return BranchStatus(info=line)

    def with_path(self, path: Path) -> "BranchStatus":
        """Return :any:`BranchStatus` with `path`."""
        # pylint: disable=unused-argument
        return self

    def has_index_changes(self):
        """Has Index Changes."""
        # pylint: disable=no-self-use
        return None


class Git:

    """
    Our Git REPO Helper.

    We know, that there are libraries for that.
    But we just want to have a lean programmatic interface to git.
    Just with the functionality **we** need. Not more.

    We currently do NOT check the git version, but try to use a quite common subset.

    The easiest way to start:

    >>> git = Git.from_path()
    """

    # pylint: disable=too-many-public-methods

    def __init__(self, path: Path):
        self.path = path

    def __repr__(self):
        return get_repr(self, (self.path,))

    @staticmethod
    def find_path(path: Optional[Path] = None) -> Path:
        """Determine Top Directory of Git Clone."""
        path = path or Path.cwd()
        result = run(("git", "rev-parse", "--show-cdup"), capture_output=True, check=False, cwd=path)
        if result.stderr:
            raise NoGitError()
        cdup = result.stdout.decode("utf-8").strip()
        return (path / cdup).resolve()

    @staticmethod
    def from_path(path: Optional[Path] = None) -> "Git":
        """Create GIT Repo Helper from `path`."""
        path = Git.find_path(path=path)
        return Git(path=path)

    def is_cloned(self) -> bool:
        """Check if clone already exists."""
        if not self.path.exists() or not self.path.is_dir():
            return False
        result = self._run(("rev-parse", "--show-cdup"), capture_output=True, check=False)
        cloned = not result.stderr and not result.stdout.strip()
        _LOGGER.info("Git(%r).is_cloned() = %r", str(self.path), cloned)
        return cloned

    def init(self, branch="main"):
        """Initialize Git Clone."""
        _LOGGER.info("Git(%r).init(branch=%r)", str(self.path), branch)
        self._run(("init", "-b", branch))

    def set_config(self, name, value):
        """Configure."""
        self._run(("config", name, value))

    def clone(self, url, revision=None):
        """Clone."""
        _LOGGER.info("Git(%r).clone(%r, revision=%r)", str(self.path), url, revision)
        if revision:
            # We do not checkout, to be faster during switch later on
            run(("git", "clone", "--no-checkout", "--", str(url), str(self.path)))
            self._run(("checkout", revision))
        else:
            run(("git", "clone", "--", str(url), str(self.path)))

    def get_tag(self) -> Optional[str]:
        """Get Actual Tag."""
        tag = self._run2str(("describe", "--exact-match", "--tags"), check=False) or None
        _LOGGER.info("Git(%r).get_tag() = %r", str(self.path), tag)
        return tag

    def get_branch(self) -> Optional[str]:
        """Get Actual Branch."""
        branch = self._run2str(("branch", "--show-current")) or None
        _LOGGER.info("Git(%r).get_branch() = %r", str(self.path), branch)
        return branch

    def get_sha(self) -> Optional[str]:
        """Get SHA."""
        sha = self._run2str(("rev-parse", "HEAD")) or None
        _LOGGER.info("Git(%r).get_sha() = %r", str(self.path), sha)
        return sha

    def get_revision(self) -> Optional[str]:
        """
        Get Revision.

        We try several things, the winner takes it all:

        1. Get Actual Tag
        2. Get Actual Branch
        3. Get SHA.
        4. `None` if empty repo.
        """
        return self.get_tag() or self.get_branch() or self.get_sha()

    def get_url(self) -> Optional[str]:
        """Get Actual URL of 'origin'."""
        url = self._run2str(("remote", "get-url", "origin"), check=False) or None
        _LOGGER.info("Git(%r).get_url() = %r", str(self.path), url)
        return url

    def checkout(self, revision: Optional[str] = None, paths: Optional[Tuple[Path, ...]] = None):
        """Checkout Revision."""
        if revision:
            self._run(("checkout", revision), paths=paths)
        else:
            self._run(("checkout",), paths=paths)
        _LOGGER.info("Git(%r).checkout(revision=%r, paths=%r)", str(self.path), revision, paths)

    def fetch(self):
        """Fetch."""
        _LOGGER.info("Git(%r).fetch()", str(self.path))
        self._run(("fetch",))

    def merge(self):
        """Merge."""
        _LOGGER.info("Git(%r).merge()", str(self.path))
        self._run(("merge",))

    def pull(self):
        """Pull."""
        _LOGGER.info("Git(%r).pull()", str(self.path))
        self._run(("pull",))

    def rebase(self):
        """Rebase."""
        _LOGGER.info("Git(%r).rebase()", str(self.path))
        self._run(("rebase",))

    def add(self, paths: Tuple[Path, ...]):
        """Add."""
        _LOGGER.info("Git(%r).add(%r)", str(self.path), paths)
        self._run(("add",), paths=paths)

    def reset(self, paths: Tuple[Path, ...]):
        """Reset."""
        _LOGGER.info("Git(%r).reset(%r)", str(self.path), paths)
        self._run(("reset",), paths=paths)

    def commit(self, msg, paths: Optional[Tuple[Path, ...]] = None):
        """Commit."""
        _LOGGER.info("Git(%r).commit(%r, paths=%r)", str(self.path), msg, paths)
        self._run(("commit", "-m", msg), paths=paths)

    def tag(self, name, msg=None):
        """Create Tag."""
        _LOGGER.info("Git(%r).tag(%r, msg=%r)", str(self.path), name, msg)
        args = ["tag", name]
        if msg:
            args += ["-m", msg]
        self._run(args)

    def status(self, branch=False) -> Generator[Status, None, None]:
        """Git Status."""
        _LOGGER.info("Git(%r).status(branch=%r)", str(self.path), branch)
        if branch:
            lines = self._run2str(("status", "--porcelain=v1", "--branch")).split("\n")
            yield BranchStatus.from_str(lines[0])
            lines = lines[1:]
        else:
            lines = self._run2str(("status", "--porcelain=v1")).split("\n")
        for line in lines:
            if line:
                yield FileStatus.from_str(line)

    def has_index_changes(self) -> bool:
        """Let you know if index has changes."""
        return any(status.has_index_changes() for status in self.status())

    def is_clean(self):
        """Clone is clean and does not contain any changes."""
        _LOGGER.info("Git(%r).is_clean()", str(self.path))
        status = self._run2str(("status", "--porcelain=v1", "--branch")).split("\n")
        if "..." in status[0]:
            return False
        if status[1:]:
            return False
        return True

    def _run(self, args: Union[List[str], Tuple[str, ...]], paths: Optional[Tuple[Path, ...]] = None, **kwargs):
        cmd = ["git"]
        cmd.extend(args)
        if paths:
            cmd.append("--")
            cmd.extend([str(path) for path in paths])
        return run(cmd, cwd=self.path, **kwargs)

    def _run2str(self, args: Union[List[str], Tuple[str, ...]], check=True) -> str:
        result = self._run(args, check=check, capture_output=True)
        if result.stderr.strip():
            return ""
        return result.stdout.decode("utf-8").rstrip()
