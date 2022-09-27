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

    """Our Git REPO Helper."""

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
        result = self._run(("rev-parse", "--show-cdup"), cwd=self.path, capture_output=True, check=False)
        return not result.stderr and not result.stdout.strip()

    def init(self):
        """Initialize."""
        self._run(("init",))

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

    def get_revision(self) -> str:
        """Get actual revision."""
        result = self._run(("branch", "--show-current"), cwd=self.path, capture_output=True)
        first_line = result.stdout.decode("utf-8").split("\n")[0]
        return first_line.rsplit(" ", 1)[-1]

    def get_url(self) -> Optional[str]:
        """Get actual url."""
        result = self._run(("remote", "get-url", "origin"), capture_output=True, check=False)
        stdout = result.stdout.strip()
        if result.stderr or not stdout:
            return None
        return result.stdout.decode("utf-8")

    def is_branch(self, revision=None) -> bool:
        """Check if `revision` is a branch."""
        revision = revision or self.get_revision()
        # TODO: is_branch
        return True

    def checkout(self, revision):
        """Checkout Revision."""
        self._run(("checkout", revision))

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

    def _run(self, cmd, cwd=None, **kwargs):
        cwd = cwd or self.path
        cmd = ("git",) + tuple(cmd)
        return run(cmd, cwd=cwd, **kwargs)
