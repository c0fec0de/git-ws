"""Git Utilities."""

import re
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

from ._basemodel import BaseModel
from ._util import get_repr, run
from .exceptions import NoGitError

_RE_STATUS = re.compile(r"\A(?P<index>.)(?P<work>.)\s((?P<orig_path>.+) -> )?(?P<path>.+)\Z")


class Status(BaseModel):

    """
    Git Status Line.

    >>> status = Status.from_str("?? file.txt")
    >>> status
    Status(index='?', work='?', path=PosixPath('file.txt'))
    >>> str(status)
    '?? file.txt'
    >>> str(status.with_path(Path("base")))
    '?? base/file.txt'

    >>> status = Status.from_str("?? src.txt -> dest.txt")
    >>> status
    Status(index='?', work='?', path=PosixPath('dest.txt'), orig_path=PosixPath('src.txt'))
    >>> str(status)
    '?? src.txt -> dest.txt'
    >>> str(status.with_path(Path("base")))
    '?? base/src.txt -> base/dest.txt'
    """

    index: str
    """Status of the Index."""

    work: str
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
    def from_str(line) -> "Status":
        """Create v1 porcelain output."""
        mat = _RE_STATUS.match(line)
        assert mat, f"Invalid pattern {line}"
        return Status(**mat.groupdict())

    def with_path(self, path: Path) -> "Status":
        """Return :any:`Status` with `path`."""
        if self.orig_path:
            return self.update(path=path / self.path, orig_path=path / self.orig_path)
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
        return not result.stderr and not result.stdout.strip()

    def init(self, branch="main"):
        """Initialize Git Clone."""
        self._run(("init", "-b", branch))

    def set_config(self, name, value):
        """Configure."""
        self._run(("config", name, value))

    def clone(self, url, revision=None):
        """Clone."""
        args = ["git", "clone"]
        if revision:
            args += ["--branch", revision]
        args += ["--", str(url), str(self.path)]
        run(args)

    def get_tag(self) -> Optional[str]:
        """Get Actual Tag."""
        return self._run2str(("describe", "--exact-match", "--tags"), check=False) or None

    def get_branch(self) -> Optional[str]:
        """Get Actual Branch."""
        return self._run2str(("branch", "--show-current")) or None

    def get_sha(self, revision="HEAD") -> Optional[str]:
        """Get SHA."""
        return self._run2str(("rev-parse", revision)) or None

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
        return self._run2str(("remote", "get-url", "origin"), check=False) or None

    def checkout(self, revision: Optional[str] = None, paths: Optional[Tuple[Path, ...]] = None):
        """Checkout Revision."""
        if revision:
            self._run(("checkout", revision), paths=paths)
        else:
            self._run(("checkout",), paths=paths)

    def fetch(self):
        """Fetch."""
        self._run(("fetch",))

    def merge(self):
        """Merge."""
        self._run(("merge",))

    def pull(self):
        """Pull."""
        self._run(("pull",))

    def rebase(self):
        """Rebase."""
        self._run(("rebase",))

    def add(self, paths: Tuple[Path, ...]):
        """Add."""
        self._run(("add",), paths=paths)

    def reset(self, paths: Tuple[Path, ...]):
        """Reset."""
        self._run(("reset",), paths=paths)

    def commit(self, msg, paths: Optional[Tuple[Path, ...]] = None):
        """Commit."""
        self._run(("commit", "-m", msg), paths=paths)

    def tag(self, name, msg=None):
        """Create Tag."""
        args = ["tag", name]
        if msg:
            args += ["-m", msg]
        self._run(args)

    def status(self) -> Generator[Status, None, None]:
        """Git Status."""
        for line in self._run2str(("status", "--porcelain=v1")).split("\n"):
            if line:
                yield Status.from_str(line)

    def is_clean(self):
        """Clone is clean and does not contain any changes."""
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
