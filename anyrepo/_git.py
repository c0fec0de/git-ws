"""Git Utilities."""

from pathlib import Path
from typing import Optional

from ._util import run
from .exceptions import NoGitError


def get_repo_top(path: Optional[Path]) -> Path:
    """Determine Git Clone Repository Top Directory."""
    path = path or Path.cwd()
    result = run(("git", "rev-parse", "--show-cdup"), capture_output=True, check=False, cwd=path)
    if result.stderr:
        raise NoGitError()
    cdup = result.stdout.decode("utf-8").strip()
    return (path / cdup).resolve()


class Git:

    """
    Our Git REPO Helper.

    We know, that there are libraries for that.
    But we just want to have a lean programmatic interface to git.
    """

    def __init__(self, path):
        self.path = path

    @staticmethod
    def from_path(path: Optional[Path]) -> "Git":
        """Create GIT Repo Helper from `path`."""
        path = get_repo_top(path=path)
        return Git(path=path)

    def is_cloned(self) -> bool:
        """Check if clone already exists."""
        if not self.path.exists() or not self.path.is_dir():
            return False
        result = self._run(("rev-parse", "--show-cdup"), capture_output=True, check=False)
        return not result.stderr and not result.stdout.strip()

    def init(self, branch="main"):
        """Initialize."""
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

    def get_branch(self) -> Optional[str]:
        """Get Branch."""
        return self._run2str(("branch", "--show-current")) or None

    def get_tag(self) -> Optional[str]:
        """Get Tag."""
        return self._run2str(("describe", "--exact-match", "--tags"), check=False) or None

    def get_sha(self, revision="HEAD") -> str:
        """Get SHA."""
        return self._run2str(("rev-parse", revision))

    def get_url(self) -> Optional[str]:
        """Get actual url."""
        return self._run2str(("remote", "get-url", "origin"), check=False) or None

    def checkout(self, revision):
        """Checkout Revision."""
        self._run(("checkout", revision))

    def fetch(self):
        """Pull."""
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

    def add(self, file):
        """Add."""
        self._run(("add", str(file)))

    def commit(self, msg):
        """Commit."""
        self._run(("commit", "-m", msg))

    def tag(self, name, msg=None):
        """Tag."""
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
