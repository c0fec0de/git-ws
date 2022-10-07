"""Clone."""

from ._util import get_repr
from .datamodel import Project
from .git import Git
from .workspace import Workspace


class Clone:

    """
    Clone.

    Args:
        project: Project
        git: Git.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, project: Project, git: Git):
        self.project = project
        self.git = git

    @staticmethod
    def from_project(workspace: Workspace, project: Project) -> "Clone":
        """Create :any:`Clone` for `project` in `workspace`."""
        project_path = workspace.get_project_path(project, relative=True)
        git = Git(project_path)
        return Clone(project, git)

    def __repr__(self):
        return get_repr(self, (self.project, self.git))
