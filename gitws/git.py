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
import os
import re
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from ._basemodel import BaseModel
from ._util import get_repr, run
from .exceptions import NoGitError

_RE_STATUS = re.compile(r"\A(?P<index>.)(?P<work>.)\s((?P<orig_path>.+) -> )?(?P<path>.+)\Z")
_RE_DIFFSTAT = re.compile(r"\A\s(?P<path>.+)\s\|\s(?P<stat>.+)\Z")
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

    def has_work_changes(self) -> Optional[bool]:
        """Has Work Changes."""
        # pylint: disable=no-self-use
        return None  # pragma: no cover

    def has_index_changes(self) -> Optional[bool]:
        """Has Index Changes."""
        # pylint: disable=no-self-use
        return None  # pragma: no cover

    def has_changes(self) -> Optional[bool]:
        """Has Changes."""
        return self.has_index_changes() or self.has_work_changes()


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

    def has_work_changes(self) -> bool:
        """Has Work Changes."""
        return self.work not in (State.UNMODIFIED, State.IGNORED, State.UNTRACKED)

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
        """Create from v1 porcelain output."""
        return BranchStatus(info=line)

    def with_path(self, path: Path) -> "BranchStatus":
        """Return :any:`BranchStatus` with `path`."""
        # pylint: disable=unused-argument
        return self


class DiffStat(BaseModel):

    """
    Diff Status.
    """

    path: Path
    """Path."""

    stat: str
    """Diff Status."""

    def __str__(self):
        return f" {self.path} | {self.stat}"

    @staticmethod
    def from_str(line) -> "DiffStat":
        """Create from `diff --stat` output."""
        mat = _RE_DIFFSTAT.match(line)
        assert mat, f"Invalid pattern {line}"
        return DiffStat(**mat.groupdict())

    def with_path(self, path: Path) -> "DiffStat":
        """Return :any:`DiffStat` with `path`."""
        return self.update(path=path / self.path)


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

    def checkout(self, revision: Optional[str] = None, paths: Optional[Tuple[Path, ...]] = None, force: bool = False):
        """Checkout Revision."""
        args = ["checkout"]
        if revision:
            args.append(revision)
        if force:
            args.append("--force")
        self._run(args, paths=paths)
        _LOGGER.info("Git(%r).checkout(revision=%r, paths=%r, force=%r)", str(self.path), revision, paths, force)

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

    def add(self, paths: Optional[Tuple[Path, ...]] = None, force: bool = False, all_: bool = False):
        """Add."""
        _LOGGER.info("Git(%r).add(%r, force=%r, all_=%r)", str(self.path), paths, force, all_)
        args = ["add"]
        if force:
            args.append("--force")
        if all_:
            args.append("--all")
        self._run(args, paths=paths)

    # pylint: disable=invalid-name
    def rm(self, paths: Tuple[Path, ...], cached: bool = False, force: bool = False, recursive: bool = False):
        """rm."""
        _LOGGER.info(
            "Git(%r).rm(%r, cached=%r, force=%r, recursive=%r)", str(self.path), paths, cached, force, recursive
        )
        args = ["rm"]
        if cached:
            args.append("--cached")
        if force:
            args.append("--force")
        if recursive:
            args.append("-r")
        self._run(args, paths=paths)

    def reset(self, paths: Tuple[Path, ...]):
        """Reset."""
        _LOGGER.info("Git(%r).reset(%r)", str(self.path), paths)
        self._run(("reset",), paths=paths)

    def commit(self, msg, paths: Optional[Tuple[Path, ...]] = None, all_: bool = False):
        """Commit."""
        _LOGGER.info("Git(%r).commit(%r, paths=%r, all_=%r)", str(self.path), msg, paths, all_)
        args = ["commit", "-m", msg]
        if all_:
            args.append("--all")
        self._run(args, paths=paths)

    def tag(self, name, msg=None):
        """Create Tag."""
        _LOGGER.info("Git(%r).tag(%r, msg=%r)", str(self.path), name, msg)
        args = ["tag", name]
        if msg:
            args += ["-m", msg]
        self._run(args)

    def status(self, paths: Optional[Tuple[Path, ...]] = None, branch: bool = False) -> Generator[Status, None, None]:
        """Git Status."""
        _LOGGER.info("Git(%r).status(paths=%r, branch=%r)", str(self.path), paths, branch)
        if branch:
            lines = self._run2str(("status", "--porcelain=v1", "--branch"), paths=paths).split("\n")
            yield BranchStatus.from_str(lines[0])
            lines = lines[1:]
        else:
            lines = self._run2str(("status", "--porcelain=v1"), paths=paths).split("\n")
        for line in lines:
            if line:
                yield FileStatus.from_str(line)

    def diff(self, paths: Optional[Tuple[Path, ...]] = None, prefix: Path = None):
        """Git Diff."""
        _LOGGER.info("Git(%r).diff(paths=%r, prefix=%r)", str(self.path), paths, prefix)
        if prefix:
            sep = os.path.sep
            src = f"a{sep}{prefix}{sep}"
            dst = f"b{sep}{prefix}{sep}"
            self._run(("diff", "--src-prefix", src, "--dst-prefix", dst))
        else:
            self._run(("diff",))

    def diffstat(self, paths: Optional[Tuple[Path, ...]] = None) -> Generator[DiffStat, None, None]:
        """Git Diff Status."""
        _LOGGER.info("Git(%r).diffstat(paths=%r)", str(self.path), paths)
        lines = self._run2str(("diff", "--stat"), paths=paths).split("\n")
        if lines:
            # skip last line for now
            for line in lines[:-1]:
                yield DiffStat.from_str(line)

    def has_index_changes(self) -> bool:
        """Let you know if index has changes."""
        return any(status.has_index_changes() for status in self.status())

    def has_work_changes(self) -> bool:
        """Let you know if work has changes."""
        return any(status.has_work_changes() for status in self.status())

    def has_changes(self) -> bool:
        """Let you know if work has changes."""
        return any(status.has_changes() for status in self.status())

    def is_empty(self):
        """Clone does not contain any changes (untracked, staged, committed)."""
        _LOGGER.info("Git(%r).is_empty()", str(self.path))
        status = self._run2str(("status", "--porcelain=v1", "--branch")).split("\n")
        if len(status) > 1:
            return False
        if self._run2str(("stash", "list")):
            return False
        if status[0].startswith("## No commits yet on "):
            return True
        if "..." not in status[0]:
            return False
        if "[ahead " in status[0]:
            return False
        return True

    def _run(self, args: Union[List[str], Tuple[str, ...]], paths: Optional[Tuple[Path, ...]] = None, **kwargs):
        cmd = ["git"]
        cmd.extend(args)
        if paths:
            cmd.append("--")
            cmd.extend([str(path) for path in paths])
        return run(cmd, cwd=self.path, **kwargs)

    def _run2str(
        self, args: Union[List[str], Tuple[str, ...]], paths: Optional[Tuple[Path, ...]] = None, check=True
    ) -> str:
        result = self._run(args, paths=paths, check=check, capture_output=True)
        if result.stderr.strip():
            return ""
        return result.stdout.decode("utf-8").rstrip()
