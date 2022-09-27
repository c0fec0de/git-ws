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

    def clone(self, url, branch=None):
        """Clone."""
        cmd = ["git", "clone"]
        if branch:
            cmd += ["--branch", branch]
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

    def checkout(self, revision):
        """Checkout Revision."""

    def _run(self, cmd, cwd=None, **kwargs):
        cwd = cwd or self.path
        cmd = ("git",) + tuple(cmd)
        return run(cmd, cwd=cwd, **kwargs)
