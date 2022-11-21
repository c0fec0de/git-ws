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
import hashlib
import logging
import os
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from ._basemodel import BaseModel
from ._util import get_repr, no_echo, run
from .appconfig import AppConfig
from .exceptions import GitCloneMissingError, NoGitError

_RE_URL = re.compile(r"\Aorigin\s+(?P<value>.+)\s+\(fetch\)\Z")
_RE_BRANCH = re.compile(r"\A\*\s(?P<value>\S+)\Z")
_RE_STATUS = re.compile(r"\A(?P<index>.)(?P<work>.)\s((?P<orig_path>.+) -> )?(?P<path>.+)\Z")
_RE_DIFFSTAT = re.compile(r"\A\s(?P<path>.+)\s\|\s(?P<stat>.+)\Z")
_LOGGER = logging.getLogger("git-ws")

Args = Union[List[str], Tuple[str, ...]]
BoolOptions = Tuple[Tuple[str, bool], ...]
Paths = Tuple[Path, ...]


class State(Enum):
    """
    Actual State (Part of `git status` line).

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
    """Status (One `git status` line."""

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
    """Status of Working Tree."""

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

    def __init__(self, path: Path, clone_cache: Optional[Path] = None, secho=None):
        self.path = path
        self.clone_cache = clone_cache
        self.secho = secho or no_echo

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
    def from_path(path: Optional[Path] = None, secho=None) -> "Git":
        """Create GIT Repo Helper from `path`."""
        path = Git.find_path(path=path)
        clone_cache = AppConfig().options.clone_cache
        return Git(path=path, clone_cache=clone_cache, secho=secho)

    def is_cloned(self) -> bool:
        """Return if clone already exists."""
        if not self.path.exists() or not self.path.is_dir():
            return False
        result = self._run(("rev-parse", "--show-cdup"), capture_output=True, check=False)
        cloned = not result.stderr and not result.stdout.strip()
        _LOGGER.info("Git(%r).is_cloned() = %r", str(self.path), cloned)
        return cloned

    def check(self):
        """Check clone."""
        if not self.is_cloned():
            raise GitCloneMissingError(self.path)

    def set_config(self, name, value):
        """Set Git Configuration `name` to `value`."""
        self._run(("config", name, value))

    def clone(self, url, revision: Optional[str] = None):
        """Clone `url` and checkout `revision`."""
        _LOGGER.info("Git(%r).clone(%r, revision=%r)", str(self.path), url, revision)
        assert not self.path.exists() or not any(self.path.iterdir())
        if self.clone_cache:
            key = hashlib.sha256(url.encode("utf-8")).hexdigest()
            cache = self.clone_cache / key
            if not cache.exists():
                self.secho("Initializing clone-cache")
                cache.mkdir(parents=True)
                run(("git", "clone", "--", str(url), str(cache)))
            else:
                self.secho("Using clone-cache")
                run(("git", "pull"), cwd=cache, capture_output=True)
            shutil.copytree(cache, self.path)
        else:
            run(("git", "clone", "--", str(url), str(self.path)))
        if revision:
            self._run(("checkout", revision), capture_output=True)

    def get_tag(self) -> Optional[str]:
        """Get Actual Tag."""
        tag = self._run2str(("describe", "--exact-match", "--tags"), check=False) or None
        _LOGGER.info("Git(%r).get_tag() = %r", str(self.path), tag)
        return tag

    def get_branch(self) -> Optional[str]:
        """Get Actual Branch."""
        branch = self._run2str(("branch",), regex=_RE_BRANCH)
        _LOGGER.info("Git(%r).get_branch() = %r", str(self.path), branch)
        return branch

    def get_sha(self) -> Optional[str]:
        """Get SHA."""
        sha = self._run2str(("rev-parse", "HEAD"), check=False) or None
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
        return self.get_branch() or self.get_tag() or self.get_sha()

    def get_url(self) -> Optional[str]:
        """Get Actual URL of 'origin'."""
        url = self._run2str(("remote", "-v"), regex=_RE_URL, check=False)
        _LOGGER.info("Git(%r).get_url() = %r", str(self.path), url)
        return url

    def checkout(self, revision: Optional[str] = None, paths: Optional[Paths] = None, force: bool = False):
        """
        Checkout Revision.

        Keyword Args:
            revision: Revision to checkout.
            paths: File Paths to checkout, otherwise entire repo.
            force: Overwrite local changes.
        """
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

    def merge(self, commit):
        """Merge."""
        _LOGGER.info("Git(%r).merge(%r)", str(self.path), commit)
        self._run(("merge", commit))

    def pull(self):
        """Pull."""
        _LOGGER.info("Git(%r).pull()", str(self.path))
        self._run(("pull",))

    def rebase(self):
        """Rebase."""
        _LOGGER.info("Git(%r).rebase()", str(self.path))
        self._run(("rebase",))

    def add(self, paths: Optional[Paths] = None, force: bool = False, all_: bool = False):
        """
        Add.

        Args:
            paths: File Paths to add.

        Keyword Args:
            force: allow adding otherwise ignored files.
            all_: add changes from all tracked and untracked files.
        """
        _LOGGER.info("Git(%r).add(%r, force=%r, all_=%r)", str(self.path), paths, force, all_)
        self._run(["add"], booloptions=(("--force", force), ("--all", all_)), paths=paths)

    # pylint: disable=invalid-name
    def rm(self, paths: Paths, cached: bool = False, force: bool = False, recursive: bool = False):
        """
        Remove.

        Keyword Args:
            cached: only remove from the index
            force: override the up-to-date check
            recursive: allow recursive removal
        """
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

    def reset(self, paths: Paths):
        """
        Reset.

        Args:
            paths: File paths.
        """
        _LOGGER.info("Git(%r).reset(%r)", str(self.path), paths)
        self._run(("reset",), paths=paths)

    def commit(self, msg: str, paths: Optional[Paths] = None, all_: bool = False):
        """
        Commit.

        Args:
            msg: Commit Message

        Keyword Args:
            paths: Paths.
            all_: commit all changed files
        """
        _LOGGER.info("Git(%r).commit(%r, paths=%r, all_=%r)", str(self.path), msg, paths, all_)
        args = ["commit", "-m", msg]
        if all_:
            args.append("--all")
        self._run(args, paths=paths)

    def tag(self, name: str, msg: Optional[str] = None, force: bool = False):
        """
        Create Tag.

        Args:
            name: Tag Name.

        Keyword Args:
            msg: Message.
            force: Replace tag if exists.
        """
        _LOGGER.info("Git(%r).tag(%r, msg=%r)", str(self.path), name, msg)
        args = ["tag", name]
        if force:
            args.append("--force")
        if msg:
            args += ["-m", msg]
        self._run(args)

    def get_tags(self, pattern: Optional[str] = None) -> Tuple[str, ...]:
        """Get Tags matching `pattern` or all."""
        cmd = ["tag", "-l"]
        if pattern:
            cmd.append(pattern)
        return tuple(self._run2lines(cmd, skip_empty=True))

    def status(self, paths: Optional[Paths] = None, branch: bool = False) -> Generator[Status, None, None]:
        """
        Git Status.

        Keyword Args:
            branch: Show branch.
        """
        _LOGGER.info("Git(%r).status(paths=%r, branch=%r)", str(self.path), paths, branch)
        if branch:
            lines = self._run2lines(("status", "--porcelain", "--branch"), paths=paths)
            yield BranchStatus.from_str(lines[0])
            lines = lines[1:]
        else:
            lines = self._run2lines(("status", "--porcelain"), paths=paths)
        for line in lines:
            if line:
                yield FileStatus.from_str(line)

    def diff(self, paths: Optional[Paths] = None, prefix: Optional[Path] = None):
        """
        Display Git Diff.

        Keyword Args:
            paths: Paths.
            prefix: Path  Prefix.
        """
        _LOGGER.info("Git(%r).diff(paths=%r, prefix=%r)", str(self.path), paths, prefix)
        if prefix:
            sep = os.path.sep
            src = f"a{sep}{prefix}{sep}"
            dst = f"b{sep}{prefix}{sep}"
            self._run(("diff", "--src-prefix", src, "--dst-prefix", dst))
        else:
            self._run(("diff",))

    def diffstat(self, paths: Optional[Paths] = None) -> Generator[DiffStat, None, None]:
        """
        Git Diff Statistics.

        Keyword Args:
            paths: Paths.
        """
        _LOGGER.info("Git(%r).diffstat(paths=%r)", str(self.path), paths)
        lines = self._run2lines(("diff", "--stat"), paths=paths)
        if lines:
            # skip last line for now
            for line in lines[:-1]:
                yield DiffStat.from_str(line)

    def submodule_update(self, init: bool = False, recursive: bool = False):
        """
        Submodule Update.

        Keyword Args:
            init: Initialize.
            recursive: Recursive.
        """
        _LOGGER.info("Git(%r).submodule_update(init=%r, recursive=%r)", str(self.path), init, recursive)
        self._run(("submodule", "update"), booloptions=(("--init", init), ("--recursive", recursive)))

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
        """
        Clone does not contain any changes.

        A clone is empty if there are:
        * no files changed
        * no commits which are not pushed yet
        * nothing stashed
        """
        _LOGGER.info("Git(%r).is_empty()", str(self.path))
        lines = self._run2lines(("status", "--porcelain", "--branch"))
        if len(lines) > 1:
            return False
        if self._run2str(("stash", "list")):
            return False
        if lines[0].startswith("## No commits yet on "):
            return True
        if "[ahead " in lines[0]:
            return False
        if not self.get_url():
            return False
        return True

    def _run(self, args: Args, paths: Optional[Paths] = None, booloptions: Optional[BoolOptions] = None, **kwargs):
        cmd = ["git"]
        cmd.extend(args)
        for name, value in booloptions or tuple():
            if value:
                cmd.append(name)
        if paths:
            cmd.append("--")
            cmd.extend([str(path) for path in paths])
        return run(cmd, cwd=self.path, secho=self.secho, **kwargs)

    def _run2str(self, args: Args, paths: Optional[Paths] = None, check=True, regex=None) -> Optional[str]:
        result = self._run(args, paths=paths, check=check, capture_output=True)
        if result.stderr.strip():
            return ""
        value = result.stdout.decode("utf-8").rstrip()
        if regex:
            for line in value.split("\n"):
                mat = regex.match(line)
                if mat:
                    return mat.group("value")
            return None
        return value

    def _run2lines(
        self, args: Args, paths: Optional[Paths] = None, check=True, regex=None, skip_empty: bool = False
    ) -> List[str]:
        result = self._run2str(args, paths=paths, check=check, regex=regex) or ""
        lines = result.split("\n")
        if skip_empty:
            lines = [line for line in lines if line]
        return lines
