"""Git Utilities."""

from pathlib import Path
from typing import Optional, Tuple

from ._util import get_repr, run
from .exceptions import NoGitError


class Git:

    """
    Our Git REPO Helper.

    We know, that there are libraries for that.
    But we just want to have a lean programmatic interface to git.
    Just with the functionality **we** need. Not more.

    We currently do NOT check the git version, but try to use a quite common subset.

    The easiest way to start:

    .. code-block:: python

        git = Git.from_path()
    """

    def __init__(self, path: Path):
        self.path = path

    def __repr__(self):
        return get_repr(self, (self.path,))

    @staticmethod
    def find_path(path: Optional[Path]) -> Path:
        """Determine Top Directory of Git Clone."""
        path = path or Path.cwd()
        result = run(("git", "rev-parse", "--show-cdup"), capture_output=True, check=False, cwd=path)
        if result.stderr:
            raise NoGitError()
        cdup = result.stdout.decode("utf-8").strip()
        return (path / cdup).resolve()

    @staticmethod
    def from_path(path: Optional[Path]) -> "Git":
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
        cmd = ["git", "clone"]
        if revision:
            cmd += ["--branch", revision]
        cmd += ["--", str(url), str(self.path)]
        run(cmd)

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

    def checkout(self, revision):
        """Checkout Revision."""
        self._run(("checkout", revision))

    def fetch(self):
        """Fetch."""
        self._run(("fetch",))

    def merge(self):
        """Merge."""
        self._run(("merge",))

    def pull(self):
        """Pull."""
        self._run(("pull",))

    def push(self):
        """Push."""
        self._run(("push",))

    def rebase(self):
        """Rebase."""
        self._run(("rebase",))

    def add(self, files: Tuple[Path]):
        """Add."""
        self._run(["add"] + [str(file) for file in files])

    def commit(self, msg):
        """Commit."""
        self._run(("commit", "-m", msg))

    def tag(self, name, msg=None):
        """Create Tag."""
        cmd = ["tag", name]
        if msg:
            cmd += ["-m", msg]
        self._run(cmd)

    def _run(self, cmd, cwd=None, **kwargs):
        cwd = cwd or self.path
        cmd = ("git",) + tuple(cmd)
        return run(cmd, cwd=cwd, **kwargs)

    def _run2str(self, cmd, cwd=None, check=True) -> str:
        result = self._run(cmd, cwd=cwd, check=check, capture_output=True)
        if result.stderr.strip():
            return ""
        stdout = result.stdout.decode("utf-8").strip()
        return stdout
