# Copyright 2022-2023 c0fec0de
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

"""
Our Git Helper.

We know, that there are libraries for that.
But we just want to have a lean programmatic interface to git.
Just with the functionality **we** need. Not more.

We currently do NOT check the git version and try to use the common subset.
"""
import hashlib
import logging
import os
import re
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from ._basemodel import BaseModel
from ._pathlock import atomic_update_or_create_path
from ._url import strip_user_password
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
    Current State (Part of `git status` line).

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
    """Status (One ``git status`` line)."""

    def with_path(self, path: Path) -> "Status":
        """Return :any:`Status` with ``path`` as prefix."""
        raise NotImplementedError()

    def has_work_changes(self) -> Optional[bool]:
        """Has Work Changes."""
        return None  # pragma: no cover

    def has_index_changes(self) -> Optional[bool]:
        """Has Index Changes."""
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
        """Create from ``git status --porcelain`` Output."""
        mat = _RE_STATUS.match(line)
        assert mat, f"Invalid pattern {line}"
        return FileStatus(**mat.groupdict())

    def with_path(self, path: Path) -> "FileStatus":
        """Return :any:`FileStatus` with ``path`` as prefix."""
        update = {
            "path": path / self.path,
        }
        if self.orig_path:
            update["orig_path"] = path / self.orig_path
        return self.model_copy(update=update)

    def has_work_changes(self) -> bool:
        """Has Work Changes."""
        return self.work not in (State.UNMODIFIED, State.IGNORED, State.UNTRACKED)

    def has_index_changes(self) -> bool:
        """Has Index Changes."""
        return self.index not in (State.UNMODIFIED, State.IGNORED, State.UNTRACKED)


class BranchStatus(Status):
    """
    Branch Status Line From ``git status`` command.

    >>> branchstatus = BranchStatus.from_str('main...origin/main')
    >>> branchstatus
    BranchStatus(info='main...origin/main')
    >>> str(branchstatus)
    'main...origin/main'
    """

    info: str
    """Branch Status String."""

    def __str__(self):
        return self.info

    @staticmethod
    def from_str(line) -> "BranchStatus":
        """Create from ``git status --porcelain`` Output."""
        return BranchStatus(info=line)

    def with_path(self, path: Path) -> "BranchStatus":
        """Return :any:`BranchStatus` with ``path`` as prefix."""
        return self


class DiffStat(BaseModel):
    """
    Diff Status Line From ``git diff --stat`` command.

    >>> diffstat = DiffStat.from_str(' path/file.txt | 16 ++++++++--------')
    >>> diffstat
    DiffStat(path=PosixPath('path/file.txt'), stat='16 ++++++++--------')
    >>> str(diffstat)
    ' path/file.txt | 16 ++++++++--------'
    >>> str(diffstat.with_path(Path('base')))
    ' base/path/file.txt | 16 ++++++++--------'
    """

    path: Path
    """File Path."""

    stat: str
    """Diff Status Line."""

    def __str__(self):
        return f" {self.path} | {self.stat}"

    @staticmethod
    def from_str(line) -> "DiffStat":
        """Create from ``git diff --stat`` Output."""
        mat = _RE_DIFFSTAT.match(line)
        assert mat, f"Invalid pattern {line}"
        return DiffStat(**mat.groupdict())

    def with_path(self, path: Path) -> "DiffStat":
        """Return :any:`DiffStat` with ``path`` as prefix."""
        return self.model_copy(update={"path": path / self.path})


class Git:
    """
    Work with git repositories.

    To initialize a git repository in the current working directory:

    >>> Git.init()
    Git(...)

    The easiest way to start with an existing clone:

    >>> git = Git.from_path()
    """

    def __init__(self, path: Path, clone_cache: Optional[Path] = None, secho=None):
        self.path = path
        self.clone_cache = clone_cache
        self.secho = secho or no_echo

    def __eq__(self, other):
        if isinstance(other, Git):
            return (self.path, self.clone_cache, self.secho) == (other.path, other.clone_cache, other.secho)
        return NotImplemented

    def __repr__(self):
        return get_repr(self, (self.path,))

    @staticmethod
    def init(path: Optional[Path] = None) -> "Git":
        """Initialize new git repository at ``path``."""
        path = path or Path.cwd()
        path.mkdir(parents=True, exist_ok=True)
        run(("git", "init"), cwd=path)
        return Git(path)

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
        """Create GIT Repo Helper from ``path``."""
        path = Git.find_path(path=path)
        clone_cache = AppConfig().options.clone_cache
        return Git(path=path, clone_cache=clone_cache, secho=secho)

    def is_cloned(self) -> bool:
        """Determine if clone already exists."""
        if not self.path.exists() or not self.path.is_dir():
            return False
        result = self._run(("rev-parse", "--show-cdup"), capture_output=True, check=False)
        cloned = not result.stderr and not result.stdout.strip()
        _LOGGER.info("Git(%r).is_cloned() = %r", str(self.path), cloned)
        return cloned

    def check(self):
        """Check Clone for Existance."""
        if not self.is_cloned():
            raise GitCloneMissingError(self.path)

    def set_config(self, name, value):
        """Set Git Configuration Variable ``name`` to ``value``."""
        self._run(("config", name, value))

    def clone(self, url, revision: Optional[str] = None, depth: Optional[int] = None):
        """
        Clone ``url`` and checkout ``revision``.

        The checkout is done to ``self.path``.
        If ``self.clone_cache`` directory path is set, the clone uses the given path as local filesystem cache.
        """
        _LOGGER.info("Git(%r).clone(%r, revision=%r, depth=%r)", str(self.path), url, revision, depth)
        assert not self.path.exists() or not any(self.path.iterdir())
        # This is bad code, because:
        # * `git clone` does have an option for SHA/tag/revision
        # * we re-use a filesystem cache for clones.
        if self.clone_cache:
            self._clone_cache(url)
            if depth:
                # strip down clone copy to given depth
                self._run(("fetch", "--depth", str(depth), "origin", revision or "HEAD"))
        elif depth and revision:
            self.path.mkdir(parents=True)
            self._run(("init",), capture_output=True)
            self._run(("remote", "add", "origin", str(url)))
            self._run(("fetch", "--depth", str(depth), "origin", revision), capture_output=True)
        elif depth:
            run(("git", "clone", "--depth", str(depth), "--", str(url), str(self.path)))
        else:
            run(("git", "clone", "--", str(url), str(self.path)))
        if revision:
            self._run(("checkout", revision), capture_output=True)

    def _clone_cache(self, url):
        baseurl = strip_user_password(url)
        # cache index
        key = hashlib.sha256(baseurl.encode("utf-8")).hexdigest()
        cache = self.clone_cache / key

        with atomic_update_or_create_path(cache) as tmp_cache:
            # Restore user/password credentials, repair corrupted cache
            if tmp_cache.exists():
                self.secho("Using clone-cache")
                try:
                    self._run(("remote", "add", "origin", str(url)), capture_output=True, cwd=tmp_cache)
                    self._run(("reset", "--hard"), capture_output=True, cwd=tmp_cache)
                    self._run(("clean", "-xdf"), capture_output=True, cwd=tmp_cache)
                except subprocess.CalledProcessError:  # pragma: no cover
                    _LOGGER.warning("Cache Entry %s is broken. Removing.", key)
                    shutil.rmtree(tmp_cache)  # broken
            # Cache Update
            if tmp_cache.exists():
                self._run(("fetch", "origin"), capture_output=True, cwd=tmp_cache)
                try:
                    branch = self._run2str(("branch",), regex=_RE_BRANCH, cwd=tmp_cache)
                    self._run(
                        ("branch", f"--set-upstream-to=origin/{branch}", branch), capture_output=True, cwd=tmp_cache
                    )
                    self._run(("merge", f"origin/{branch}"), capture_output=True, cwd=tmp_cache)
                except subprocess.CalledProcessError:  # pragma: no cover
                    _LOGGER.warning("Cache Entry %s is broken. Removing.", key)
                    shutil.rmtree(tmp_cache)  # broken
            # (Re-)Init Cache
            if not tmp_cache.exists():
                self.secho("Initializing clone-cache")
                tmp_cache.mkdir(parents=True)
                run(("git", "clone", "--", str(url), str(tmp_cache)))
            _LOGGER.debug("Copy %s to  %s)", tmp_cache, self.path)
            shutil.copytree(tmp_cache, self.path)
            # Remove user/password credentials from cache
            self._run(("remote", "remove", "origin"), cwd=tmp_cache)

    def get_tag(self) -> Optional[str]:
        """Get Current Tag."""
        tag = self._run2str(("describe", "--exact-match", "--tags"), check=False) or None
        _LOGGER.info("Git(%r).get_tag() = %r", str(self.path), tag)
        return tag

    def get_branch(self) -> Optional[str]:
        """Get Current Branch."""
        branch = self._run2str(("branch",), regex=_RE_BRANCH)
        _LOGGER.info("Git(%r).get_branch() = %r", str(self.path), branch)
        return branch

    def get_sha(self, revision: Optional[str] = None) -> Optional[str]:
        """Get Current SHA."""
        sha = self._run2str(("rev-parse", revision or "HEAD"), check=False) or None
        _LOGGER.info("Git(%r).get_sha(%r) = %r", str(self.path), revision, sha)
        return sha

    def get_revision(self) -> Optional[str]:
        """
        Get Revision.

        We try several things, the winner takes it all:

        1. Get Current Tag
        2. Get Current Branch
        3. Get SHA.
        4. ``None`` if empty repo.
        """
        return self.get_branch() or self.get_tag() or self.get_sha()

    def get_upstream_branch(self) -> Optional[str]:
        """Get Current Upstream Branch."""
        branch = self._run2str(("branch", "--format", "%(HEAD) %(upstream:short)"), regex=_RE_BRANCH)
        _LOGGER.info("Git(%r).get_upstream_branch() = %r", str(self.path), branch)
        return branch

    def get_url(self) -> Optional[str]:
        """Get Current URL of ``origin``."""
        url = self._run2str(("remote", "-v"), regex=_RE_URL, check=False)
        _LOGGER.info("Git(%r).get_url() = %r", str(self.path), url)
        return url

    def checkout(
        self,
        revision: Optional[str] = None,
        paths: Optional[Paths] = None,
        branch: Optional[str] = None,
        force: bool = False,
    ):
        """
        Checkout Revision.

        Keyword Args:
            revision: Revision to checkout.
            paths: File Paths to checkout, otherwise entire repo.
            branch: Branch to be checked out.
            force: Overwrite local changes.
        """
        args = ["checkout"]
        if revision:
            args.append(revision)
        if branch:
            args.append("-b")
            args.append(branch)
        if force:
            args.append("--force")
        self._run(args, paths=paths)
        _LOGGER.info("Git(%r).checkout(revision=%r, paths=%r, force=%r)", str(self.path), revision, paths, force)

    def fetch(self, shallow: Optional[str] = None, unshallow: bool = False):
        """Fetch."""
        _LOGGER.info("Git(%r).fetch(shallow=%r)", str(self.path), shallow)
        assert not shallow or not unshallow, "shallow and unshallow are mutally exclusive"
        if shallow:
            self._run(("fetch", "origin", shallow))
        elif unshallow:
            self._run(("fetch", "--unshallow"))
        else:
            self._run(("fetch",))

    def merge(self, commit):
        """Merge."""
        _LOGGER.info("Git(%r).merge(%r)", str(self.path), commit)
        self._run(("merge", commit))

    def rebase(self):
        """Rebase."""
        _LOGGER.info("Git(%r).rebase()", str(self.path))
        self._run(("rebase",))

    def add(self, paths: Optional[Paths] = None, force: bool = False, all_: bool = False):
        """
        Add Files.

        Args:
            paths: File Paths to add.

        Keyword Args:
            force: allow adding otherwise ignored files.
            all_: add changes from all tracked and untracked files.
        """
        _LOGGER.info("Git(%r).add(%r, force=%r, all_=%r)", str(self.path), paths, force, all_)
        self._run(["add"], booloptions=(("--force", force), ("--all", all_)), paths=paths)

    def rm(self, paths: Paths, cached: bool = False, force: bool = False, recursive: bool = False):
        """
        Remove Files.

        Args:
            paths: files and/or directories to be removed

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
        Reset Files.

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
        """Get Tags matching ``pattern`` or all."""
        cmd = ["tag", "-l"]
        if pattern:
            cmd.append(pattern)
        return tuple(self._run2lines(cmd, skip_empty=True))

    def status(self, paths: Optional[Paths] = None, branch: bool = False) -> Generator[Status, None, None]:
        """
        Git Status.

        Keyword Args:
            paths: files and/or directories to be checked
            branch: Show branch too.
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
        lines = self._run2lines(("diff", "--stat"), paths=paths)[:-1]
        for line in lines:
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
        if lines[0].startswith("## No commits yet on "):  # pragma: no cover
            return True
        if "[ahead " in lines[0]:
            return False
        if not self.get_url():
            return False
        return True

    def get_shallow(self) -> Optional[str]:
        """Get Shallow."""
        try:
            return (self.path / ".git" / "shallow").read_text()
        except FileNotFoundError:
            return None

    def _run(
        self,
        args: Args,
        paths: Optional[Paths] = None,
        booloptions: Optional[BoolOptions] = None,
        cwd: Optional[Path] = None,
        **kwargs,
    ):
        cmd = ["git"]
        cmd.extend(args)
        for name, value in booloptions or ():
            if value:
                cmd.append(name)
        if paths:
            cmd.append("--")
            cmd.extend([str(path) for path in paths])
        cwd = cwd or self.path
        return run(cmd, cwd=cwd, secho=self.secho, **kwargs)

    def _run2str(self, args: Args, paths: Optional[Paths] = None, check=True, regex=None, **kwargs) -> Optional[str]:
        result = self._run(args, paths=paths, check=check, capture_output=True, **kwargs)
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
