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

""":any:`Manifest` and :any:`Project` Iterators."""
import logging
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from ._util import resolve_relative
from .datamodel import Manifest, ManifestSpec, Project
from .exceptions import ManifestNotFoundError
from .filters import default_filter
from .git import Git
from .types import ProjectFilter
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")
_MANIFEST_DEFAULT = ManifestSpec()


class ManifestIter:
    """
    Iterate over all :any:`Manifest` s.

    The iterator takes a `workspace` and the path to a manifest file (`manifest_path`) of the main project.
    The manifest is read (:any:`ManifestSpec`) and translated to a :any:`Manifest`, which is yielded.
    The manifest files of the dependencies are also read, translated to a :any:`Manifest` and yielded likewise,
    until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified attributes (i.e. revision).

    Args:
        workspace: The actual workspace
        manifest_path: Path to the manifest file **in the main project**.

    Keyword Args:
        filter_: Filter function. Only projects where the filter method returns `True` on, are evaluated.

    Yields:
        Manifest
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, workspace: Workspace, manifest_path: Path, filter_: Optional[ProjectFilter] = None):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.filter_: ProjectFilter = filter_ or default_filter
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Manifest, None, None]:
        yield from self.__iter(self.manifest_path)

    def __iter(self, manifest_path: Path) -> Generator[Manifest, None, None]:
        deps: List[Path] = []
        done: List[str] = self.__done
        filter_ = self.filter_

        try:
            manifest_spec = ManifestSpec.load(manifest_path)
        except ManifestNotFoundError:
            return
        manifest = Manifest.from_spec(manifest_spec, path=str(manifest_path))
        _LOGGER.debug("%r", manifest)
        yield manifest

        for dep_project in manifest.dependencies:
            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            if not filter_(dep_project):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            _LOGGER.debug("%r", dep_project)
            dep_project_path = self.workspace.get_project_path(dep_project)

            # Recursive
            dep_manifest_path = dep_project_path / dep_project.manifest_path
            if dep_manifest_path.exists():
                deps.append(dep_manifest_path)

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_manifest_path in deps:
            yield from self.__iter(dep_manifest_path)


class ProjectIter:
    """
    Iterate over all :any:`Project` s.

    The iterator takes a `workspace` and the path to a manifest file (`manifest_path`) of the main project.
    The manifest is read (:any:`ManifestSpec`) and all dependencies are translated to :any:`Project` s, which are
    yielded.
    The manifest files of the dependencies are also read, translated to a :any:`Project` s and yielded likewise,
    until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified attributes (i.e. revision).

    Args:
        workspace: The actual workspace
        manifest_path: Path to the manifest file **in the main project**.

    Keyword Args:
        filter_: Filter function. Only projects where the filter method returns `True` on, are evaluated.
        skip_main: Do not yield main project.
        resolve_url: Resolve relative URLs to absolute ones.

    Yields:
        Project
    """

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        workspace: Workspace,
        manifest_path: Path,
        filter_: Optional[ProjectFilter] = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.filter_: ProjectFilter = filter_ or default_filter
        self.skip_main: bool = skip_main
        self.resolve_url: bool = resolve_url
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Project, None, None]:
        workspace = self.workspace
        info = workspace.info
        self.__done = [str(info.main_path)]
        if not self.skip_main:
            project = Project(name=info.main_path.name, path=str(info.main_path), is_main=True)
            if self.filter_(project):
                yield project
        try:
            manifest_spec = ManifestSpec.load(self.manifest_path)
        except ManifestNotFoundError:
            pass
        else:
            yield from self.__iter(self.workspace.main_path, manifest_spec)

    def __iter(self, project_path: Path, manifest_spec: ManifestSpec) -> Generator[Project, None, None]:
        deps: List[Tuple[Path, ManifestSpec]] = []
        refurl: Optional[str] = None
        filter_ = self.filter_
        done: List[str] = self.__done
        if self.resolve_url and manifest_spec.dependencies:
            git = Git(resolve_relative(project_path))
            refurl = git.get_url()

        _LOGGER.debug("%r", manifest_spec)

        for spec in manifest_spec.dependencies:
            dep_project = Project.from_spec(manifest_spec, spec, refurl=refurl)

            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            dep_project_path = self.workspace.get_project_path(dep_project)
            if not filter_(dep_project):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            _LOGGER.debug("%r", dep_project)
            yield dep_project

            # Recursive
            dep_manifest_path = dep_project_path / dep_project.manifest_path
            try:
                dep_manifest = ManifestSpec.load(dep_manifest_path)
            except ManifestNotFoundError:
                pass
            else:
                deps.append((dep_project_path, dep_manifest))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_project_path, dep_manifest in deps:
            yield from self.__iter(dep_project_path, dep_manifest)
