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
A Clone.

A :any:`Clone` is just the assembly of a :any:`Project` and its corresponding git interface (:any:`Git`).
"""

import logging
from contextlib import suppress
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple

from ._util import get_repr
from .appconfig import AppConfig
from .datamodel import Project
from .git import Git
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")


class Clone:
    """
    Clone - A Pair Of Project Definition And Git Interface.

    Args:
        project: Project Definition.
        git: Git Interface.
    """

    def __init__(self, project: Project, git: Git):
        self.project = project
        self.git = git

    @staticmethod
    def from_project(workspace: Workspace, project: Project, secho=None) -> "Clone":
        """Create :any:`Clone` for ``project`` in ``workspace``."""
        project_path = workspace.get_project_path(project, relative=True)
        clone_cache = AppConfig().options.clone_cache
        git = Git(project_path, clone_cache=clone_cache, secho=secho)
        return Clone(project, git)

    def check(self, exists=True, diff=True):
        """
        Check Clone And Emit Warnings On Logger.

        The following checks are processed:

        * Check that the git clone exists (if ``exists=True``).
        * Check that the current git clone revision matches the ``project.revision`` (if ``diff=True``).
        * The revision check is skipped on the main project.

        Keyword Args:
            exists: Check if cloned.
            diff: Check if revisions differ
        """
        git = self.git
        # exists
        if exists:
            git.check()
        project = self.project
        info = project.info
        # revision
        if project.revision:
            if diff:
                self._check_revision()
        elif not project.is_main:
            _LOGGER.warning("Clone %s has no revision!", info)
        # URL
        if diff and project.url:
            cloneurl = None
            with suppress(FileNotFoundError):
                cloneurl = git.get_url()
            if project.url != cloneurl:
                if cloneurl:
                    _LOGGER.warning("Clone %s remote origin is %r but intends to be: %r", info, cloneurl, project.url)
                else:
                    _LOGGER.warning("Clone %s has no remote origin but intends to be: %r", info, project.url)

    def _check_revision(self) -> None:
        git = self.git
        project = self.project
        revs: Tuple[str, ...] = ()
        with suppress(FileNotFoundError):
            # We cannot determine if we checked out a tag or SHA, so we need to be careful here
            branch = git.get_branch()
            if branch:
                revs = (branch,)
            else:
                tag = git.get_tag()
                sha = git.get_sha()
                if tag and sha:
                    revs = (tag, sha)
                elif tag:
                    revs = (tag,)
                elif sha:
                    revs = (sha,)
        if revs and project.revision not in revs:
            akas = " aka ".join(repr(rev) for rev in revs)
            _LOGGER.warning("Clone %s is on different revision: %s", project.info, akas)

    def __eq__(self, other):
        if isinstance(other, Clone):
            return (self.project, self.git) == (other.project, other.git)
        return NotImplemented

    def __repr__(self):
        return get_repr(self, (self.project, self.git))

    @property
    def info(self):
        """
        `repr`-like info string but more condensed.

        >>> import gitws
        >>> project = gitws.Project(name='pname', level=0, path='ppath', revision='prevision')
        >>> git = gitws.Git('gpath')
        >>> clone = gitws.Clone(project, git)
        >>> clone.info
        "gpath ('pname', revision='prevision')"
        """
        project = self.project
        path = str(self.git.path)
        options = get_repr(
            args=(project.name,),
            kwargs=(
                ("revision", project.revision, None),
                ("groups", ",".join(project.groups), ""),
                ("submodules", project.submodules, True),
            ),
        )
        if project.is_main:
            options = f"MAIN {options}"
        return f"{path} ({options})"


ClonePaths = Tuple[Clone, Tuple[Path, ...]]


def map_paths(clones: Tuple[Clone, ...], paths: Optional[Tuple[Path, ...]]) -> Generator[ClonePaths, None, None]:
    """
    Map ``paths`` to ``clones``.

    Associate the given ``paths`` to the corresponding ``clones``.

    * If ``paths`` is not empty, the corresponding clone and paths pairs are yielded.
    * If ``paths`` is empty, just all clones with an empty paths tuple are yielded.
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
        nopaths: Tuple[Path, ...] = ()
        for clone in clones:
            yield clone, nopaths


CloneFilter = Callable[[Clone], bool]


def filter_clone_on_branch(clone: Clone) -> bool:
    """Return `True` on branches."""
    return bool(clone.git.get_branch())
