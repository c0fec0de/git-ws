"""
Clone.

A :any:`Clone` is just the assembly of a :any:`Project` and its corresponding git interface (:any:`Git`).
"""

from pathlib import Path
from typing import Generator, List, Tuple

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


ClonePaths = Tuple[Clone, Tuple[Path, ...]]


def map_paths(clones: Tuple[Clone, ...], paths: Tuple[Path, ...]) -> Generator[ClonePaths, None, None]:
    """Map `paths` to `clones`."""
    clonepaths: Tuple[Tuple[Clone, List[Path]], ...] = tuple((clone, []) for clone in clones)
    # We operate on the absolute paths, but keep track of the specified ones.
    origpaths: List[Path] = list(paths)
    abspaths: List[Path] = [path.resolve() for path in paths]
    # Start path matching at the clones with the deepest folder
    clonepathssorted = sorted(clonepaths, key=lambda item: item[0].git.path.resolve().parts, reverse=True)
    # Matching
    for item in clonepathssorted:
        clone: Clone = item[0]
        cpaths: List[Path] = item[1]
        clonepath = clone.git.path.resolve()
        for path in tuple(abspaths):
            try:
                relpath = path.relative_to(clonepath)
            except ValueError:
                continue
            # pop file from list
            idx = abspaths.index(path)
            origpaths.pop(idx)
            abspaths.pop(idx)
            cpaths.append(relpath)

    # Report non-matching
    for path in origpaths:
        raise ValueError(f"{str(path)!r} cannot be associated with any clone.")

    # Return
    for clone, cpaths in clonepaths:
        yield clone, tuple(cpaths)
