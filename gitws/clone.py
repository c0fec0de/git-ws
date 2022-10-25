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

"""
Clone.

A :any:`Clone` is just the assembly of a :any:`Project` and its corresponding git interface (:any:`Git`).
"""

from pathlib import Path
from typing import Generator, List, Optional, Tuple

from ._util import get_repr
from .datamodel import Project
from .git import Git
from .workspace import Workspace


class Clone:

    """
    Clone - A Pair Of Project And Git Interface.

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

    @property
    def info(self):
        """
        `repr`-like info string but more condensed.
        """
        project = self.project
        path = str(self.git.path)
        if project.is_main:
            options = "MAIN"
        else:
            args = (project.name,) if project.name != path else tuple()
            options = get_repr(
                args=args,
                kwargs=(
                    ("revision", project.revision, None),
                    ("groups", ",".join(group.info for group in project.groups), ""),
                ),
            )
        if options:
            return f"{path} ({options})"
        return path


ClonePaths = Tuple[Clone, Tuple[Path, ...]]


def map_paths(clones: Tuple[Clone, ...], paths: Optional[Tuple[Path, ...]]) -> Generator[ClonePaths, None, None]:
    """
    Map `paths` to `clones`.

    Associate the given `paths` to the corresponding `clones`.

    If `paths` is not empty, the corresponding clone and paths pairs are yielded.
    If `paths` is empty, just all clones with an empty paths tuple are yielded.
    """
    if paths:
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
            if cpaths:
                yield clone, tuple(cpaths)
    else:
        nopaths: Tuple[Path, ...] = tuple()
        for clone in clones:
            yield clone, nopaths
