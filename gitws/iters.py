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
Helpers to iterate over all :any:`Manifest` or :any:`Project` instances.

Please note, these iterators require a :any:`Workspace` with existing manifest files within.
The creation/cloning of missing project dependencies during the iteration is supported.
"""
import logging
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple

from ._util import resolve_relative
from .datamodel import GroupFilters, Groups, GroupSelects, Manifest, ManifestSpec, Project
from .exceptions import GitCloneMissingOriginError, ManifestNotFoundError
from .git import Git
from .manifestfinder import find_manifest
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")
FilterFunc = Callable[[str, Groups], bool]


class ManifestIter:
    """
    Iterate over all :any:`Manifest` s.

    The iterator takes a :any:`Workspace` and the path to a manifest file (`manifest_path`) of the main project.
    The manifest is read (:any:`ManifestSpec`) and translated to a :any:`Manifest`, which is yielded.
    The manifest files of the dependencies are also read, translated to a :any:`Manifest` and yielded likewise,
    until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified attributes (i.e. revision).

    Args:
        workspace: The actual workspace
        manifest_path: Path to the manifest file.
        group_filters: Group Filters.

    Yields:
        :any:`Manifest`
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, workspace: Workspace, manifest_path: Path, group_filters: GroupFilters):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.group_filters: GroupFilters = group_filters
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Manifest, None, None]:
        self.__done.clear()
        try:
            manifest_spec = ManifestSpec.load(self.manifest_path)
        except ManifestNotFoundError:
            pass
        else:
            group_filters: GroupFilters = manifest_spec.group_filters + self.group_filters  # type: ignore
            group_selects = GroupSelects.from_group_filters(group_filters)
            filter_ = create_filter(group_selects, default=True)
            yield from self.__iter(self.manifest_path, manifest_spec, filter_)

    def __iter(
        self, manifest_path: Path, manifest_spec: ManifestSpec, filter_: FilterFunc
    ) -> Generator[Manifest, None, None]:
        deps: List[Tuple[Path, ManifestSpec, GroupSelects]] = []
        done: List[str] = self.__done

        manifest = Manifest.from_spec(manifest_spec, path=str(manifest_path))
        _LOGGER.debug("%r", manifest)
        yield manifest

        for dep_project in manifest.dependencies:
            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            if not filter_(dep_project.path, dep_project.groups):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            # Recursive
            dep_project_path = self.workspace.get_project_path(dep_project)
            dep_manifest_path = dep_project_path / (find_manifest(dep_project_path) or dep_project.manifest_path)
            try:
                dep_manifest_spec = ManifestSpec.load(dep_manifest_path)
            except ManifestNotFoundError:
                pass
            else:
                group_selects = GroupSelects.from_groups(dep_project.with_groups)
                deps.append((dep_manifest_path, dep_manifest_spec, group_selects))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_manifest_path, dep_manifest_spec, dep_group_selects in deps:
            dep_filter = create_filter(dep_group_selects)
            yield from self.__iter(dep_manifest_path, dep_manifest_spec, dep_filter)


class ProjectIter:
    """
    Iterate over all :any:`Project` s.

    The iterator takes a :any:`Workspace` and the path to a manifest file (`manifest_path`) of the main project.
    The manifest is read (:any:`ManifestSpec`) and all dependencies are translated to :any:`Project` s, which are
    yielded.
    The manifest files of the dependencies are also read, translated to a :any:`Project` s and yielded likewise,
    until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified attributes (i.e. revision).

    Args:
        workspace: The actual workspace
        manifest_path: Path to the manifest file **in the main project**.
        group_filters: Group Filters.

    Keyword Args:
        skip_main: Do not yield main project.
        resolve_url: Resolve relative URLs to absolute ones.

    Yields:
        :any:`Project`
    """

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        workspace: Workspace,
        manifest_path: Path,
        group_filters: GroupFilters,
        skip_main: bool = False,
        resolve_url: bool = False,
    ):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.group_filters: GroupFilters = group_filters
        self.skip_main: bool = skip_main
        self.resolve_url: bool = resolve_url
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Project, None, None]:
        workspace = self.workspace
        info = workspace.info
        main_path_rel = str(info.main_path or "")
        self.__done = [main_path_rel]
        try:
            manifest_spec = ManifestSpec.load(self.manifest_path)
        except ManifestNotFoundError:
            manifest_spec = ManifestSpec()
        main_path = workspace.main_path
        if main_path and not self.skip_main:
            main_git = Git(resolve_relative(main_path))
            revision = main_git.get_revision()
            yield Project(
                name=main_path.name,
                path=main_path_rel,
                revision=revision,
                linkfiles=manifest_spec.linkfiles,
                copyfiles=manifest_spec.copyfiles,
                is_main=True,
            )
        if manifest_spec.dependencies:
            group_filters: GroupFilters = manifest_spec.group_filters + self.group_filters  # type: ignore
            group_selects = GroupSelects.from_group_filters(group_filters)
            filter_ = create_filter(group_selects, default=True)
            yield from self.__iter(main_path, manifest_spec, filter_)

    def __iter(
        self, project_path: Optional[Path], manifest_spec: ManifestSpec, filter_: FilterFunc
    ) -> Generator[Project, None, None]:
        # pylint: disable=too-many-locals
        deps: List[Tuple[Path, ManifestSpec, GroupSelects]] = []
        refurl: Optional[str] = None
        done: List[str] = self.__done
        if project_path and manifest_spec.dependencies:
            project_path_rel = resolve_relative(project_path)
            git = Git(project_path_rel)
            refurl = git.get_url()
            if not refurl:
                raise GitCloneMissingOriginError(project_path_rel)

        _LOGGER.debug("%r", manifest_spec)

        for spec in manifest_spec.dependencies:
            dep_project = Project.from_spec(manifest_spec, spec, refurl=refurl, resolve_url=self.resolve_url)

            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            if not filter_(dep_project.path, dep_project.groups):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            _LOGGER.debug("%r", dep_project)
            yield dep_project

            # Recursive
            dep_project_path = self.workspace.get_project_path(dep_project)
            dep_manifest_path = dep_project_path / (find_manifest(dep_project_path) or dep_project.manifest_path)
            try:
                dep_manifest = ManifestSpec.load(dep_manifest_path)
            except ManifestNotFoundError:
                pass
            else:
                group_selects = GroupSelects.from_groups(dep_project.with_groups)
                deps.append((dep_project_path, dep_manifest, group_selects))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_project_path, dep_manifest, dep_group_selects in deps:
            dep_filter = create_filter(dep_group_selects)
            yield from self.__iter(dep_project_path, dep_manifest, dep_filter)


def create_filter(group_selects: GroupSelects, default: bool = False) -> FilterFunc:
    """
    Create Group Filter Function.

    Filter projects based on their ``path`` and ``groups``.
    The filter has ``group_selects``, a specification which groups should be included or excluded.
    The default selection of these groups is controlled by ``default``.

    Keyword Args:
        group_selects: Iterable with :any:`GroupSelect`.
        default: Default selection of all ``groups``.

    >>> group_filters = ('-@special', '+test', '+doc', '+feature@dep', '-doc')
    >>> group_selects = GroupSelects.from_group_filters(group_filters)
    >>> groupfilter = create_filter(group_selects)
    >>> groupfilter('sub', tuple())  # selected as there is no group
    True
    >>> groupfilter('sub', ('foo', 'bar'))  # no group selected by group_filters
    False
    >>> groupfilter('sub', ('test',))  # 'test' is selected by group_filters
    True
    >>> groupfilter('sub', ('doc',))  # 'doc' is deselected by group_filters
    False
    >>> groupfilter('sub', ('test', 'doc'))  # 'test' is selected by group_filters
    True
    >>> groupfilter('sub', ('feature',))  # 'feature' is only selected for 'dep', but not 'sub'
    False
    >>> groupfilter('dep', ('feature',))  # 'feature' is only selected for 'dep'
    True
    >>> groupfilter('special', tuple())  # deselected, even without group
    False
    >>> groupfilter('special', ('foo', 'bar'))  # deselected
    False
    >>> groupfilter('special', ('test', 'bar'))  # deselected, but overwritten by '+test'
    True

    The same, but with ``default=True``:

    >>> groupfilter = create_filter(group_selects, default=True)
    >>> groupfilter('sub', tuple())  # selected as there is no group
    True
    >>> groupfilter('sub', ('foo', 'bar'))  # no group selected by group_filters, but `default=True`
    True
    >>> groupfilter('sub', ('test',))  # 'test' is selected by group_filters
    True
    >>> groupfilter('sub', ('doc',))  # 'doc' is deselected by group_filters
    False
    >>> groupfilter('sub', ('test', 'doc'))  # 'test' is selected by group_filters
    True
    >>> groupfilter('sub', ('feature',))  # 'feature' is only selected for 'dep', but not 'sub', but `default=True`
    True
    >>> groupfilter('dep', ('feature',))  # 'feature' is only selected for 'dep'
    True
    >>> groupfilter('special', tuple())  # deselected, even without group
    False
    >>> groupfilter('special', ('foo', 'bar'))  # deselected
    False
    >>> groupfilter('special', ('test', 'bar'))  # deselected, but overwritten by '+test'
    True
    """

    if group_selects:

        def filter_(path: str, groups: Groups):
            if groups:
                selects = {group: default for group in groups}
            else:
                selects = {None: True}
            for group_select in group_selects:
                group = group_select.group
                if group and group not in selects:
                    # not relevant group name
                    continue
                if group_select.path and not fnmatchcase(path, group_select.path):
                    # not relevant path
                    continue
                if group:
                    selects[group] = group_select.select
                else:
                    selects = {group: group_select.select for group in selects}
            return any(selects.values())

    else:

        def filter_(path: str, groups: Groups):
            # pylint: disable=unused-argument
            if groups:
                return default
            return True

    return filter_
