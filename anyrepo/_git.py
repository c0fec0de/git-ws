"""Git Utilities."""

from pathlib import Path
from typing import Optional

from ._util import run
from .exceptions import NoGitError


def get_repo_top(path: Optional[Path]) -> Path:
    """Determine Git Clone Repository Top Directory."""
    path = path or Path.cwd()
    result = run(("git", "rev-parse", "--show-cdup"), capture_output=True, check=False)
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

    def get_revision(self):
        """Get Revision."""
        result = run(("git", "branch", "--show-current"), cwd=self.path, capture_output=True)
        first_line = result.stdout.decode("utf-8").split("\n")[0]
        return first_line.rsplit(" ", 1)[-1]
