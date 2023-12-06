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
Helpers to iterate over all :py:class:`gitws.Manifest` or :py:class:`gitws.Project` instances.

Please note, these iterators require a :py:class:`gitws.Workspace` with existing manifest files within.
The creation/cloning of missing project dependencies during the iteration is supported.
"""
import logging
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple

from ._manifestformatmanager import ManifestFormatManager
from ._util import resolve_relative
from .datamodel import (
    GroupFilters,
    Groups,
    GroupSelects,
    Manifest,
    ManifestSpec,
    Project,
    group_selects_from_filters,
    group_selects_from_groups,
)
from .exceptions import GitCloneMissingOriginError, ManifestNotFoundError
from .git import Git
from .manifestfinder import find_manifest
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")
GroupFilterFunc = Callable[[str, Groups], bool]
ProjectFilterFunc = Callable[[Project], bool]


class ManifestIter:
    """
    Iterate over all :py:class:`gitws.Manifest` s.

    The iterator takes a :py:class:`gitws.Workspace` and the path to a manifest file (`manifest_path`)
    of the main project.
    The manifest is read (:py:class:`gitws.ManifestSpec`) and translated to a :py:class:`gitws.Manifest`,
    which is yielded.
    The manifest files of the dependencies are also read, translated to a :py:class:`gitws.Manifest` and
    yielded likewise, until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified attributes (i.e. revision).

    Args:
        workspace: The current workspace
        manifest_path: Path to the manifest file.
        group_filters: Group Filters.

    Yields:
        :py:class:`gitws.Manifest`
    """

    def __init__(
        self,
        workspace: Workspace,
        manifest_format_manager: ManifestFormatManager,
        manifest_path: Path,
        group_filters: GroupFilters,
    ):
        self.workspace: Workspace = workspace
        self.manifest_format_manager = manifest_format_manager
        self.manifest_path: Path = manifest_path
        self.group_filters: GroupFilters = group_filters
        self.__done: List[str] = []

    def __iter__(self) -> Iterator[Manifest]:
        self.__done.clear()
        try:
            manifest_spec = self.manifest_format_manager.load(self.manifest_path)
        except ManifestNotFoundError:
            pass
        else:
            group_filters: GroupFilters = manifest_spec.group_filters + self.group_filters
            group_selects = group_selects_from_filters(group_filters)
            filter_ = create_filter(group_selects, default=True)
            yield from self.__iter(self.manifest_path, manifest_spec, filter_)

    def __iter(self, manifest_path: Path, manifest_spec: ManifestSpec, filter_: GroupFilterFunc) -> Iterator[Manifest]:
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

            if not dep_project.recursive:
                _LOGGER.debug("NON-RECURSIVE %r", dep_project)
                continue

            # Recursive
            dep_project_path = self.workspace.get_project_path(dep_project)
            dep_manifest_path = dep_project_path / (find_manifest(dep_project_path) or dep_project.manifest_path)
            try:
                dep_manifest_spec = self.manifest_format_manager.load(dep_manifest_path)
            except ManifestNotFoundError:
                pass
            else:
                group_selects = group_selects_from_groups(dep_project.with_groups)
                deps.append((dep_manifest_path, dep_manifest_spec, group_selects))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_manifest_path, dep_manifest_spec, dep_group_selects in deps:
            dep_filter = create_filter(dep_group_selects)
            yield from self.__iter(dep_manifest_path, dep_manifest_spec, dep_filter)


class ProjectLevelIter:
    """
    Iterate over all :py:class:`gitws.Project` s.

    The iterator takes a :py:class:`gitws.Workspace` and the path to a manifest file (`manifest_path`)
    of the main project.
    The manifest is read (:py:class:`gitws.ManifestSpec`) and all dependencies are translated to
    :py:class:`gitws.Project` s, which are yielded.
    The manifest files of the dependencies are also read, translated to a :py:class:`gitws.Project` s
    and yielded likewise, until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified
    attributes (i.e. revision).

    Args:
        workspace: The current workspace
        manifest_path: Path to the manifest file **in the main project**.
        group_filters: Group Filters.

    Keyword Args:
        skip_main: Do not yield main project.
        resolve_url: Resolve relative URLs to absolute ones.

    Yields:
        :py:class:`Tuple[gitws.Project, ...]`
    """

    def __init__(
        self,
        workspace: Workspace,
        manifest_format_manager: ManifestFormatManager,
        manifest_path: Path,
        group_filters: GroupFilters,
        filter_: Optional[ProjectFilterFunc] = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ):
        self.workspace: Workspace = workspace
        self.manifest_format_manager: ManifestFormatManager = manifest_format_manager
        self.manifest_path: Path = manifest_path
        self.group_filters: GroupFilters = group_filters
        self.filter_: Optional[ProjectFilterFunc] = filter_
        self.skip_main: bool = skip_main
        self.resolve_url: bool = resolve_url

    def __iter__(self) -> Iterator[Tuple[Project, ...]]:  # noqa: C901, PLR0915, PLR0912
        # NOTE: This is a quite long and complex method - on purpose - optimized for speed

        workspace = self.workspace
        info = workspace.info
        main_path_rel = str(info.main_path or "")
        done = [main_path_rel]
        main_path = workspace.main_path
        project_filter = self.filter_ or (lambda _: True)

        # level=0
        if main_path and not self.skip_main:
            main_git = Git(resolve_relative(main_path))
            revision = main_git.get_revision()
            project = Project(
                name=main_path.name,
                path=main_path_rel,
                level=0,
                revision=revision,
                is_main=True,
            )
            if project_filter(project):
                yield (project,)
        try:
            manifest_spec = self.manifest_format_manager.load(self.manifest_path)
        except ManifestNotFoundError:
            manifest_spec = ManifestSpec()
        if not manifest_spec.dependencies:
            return

        # Start Iteration
        group_filters: GroupFilters = manifest_spec.group_filters + self.group_filters
        group_selects = group_selects_from_filters(group_filters)
        group_filter = create_filter(group_selects, default=True)
        manifests = [(main_path, manifest_spec, group_filter)]
        projects: List[Project] = []
        level = 1

        while manifests:
            for project_path, manifest_spec, group_filter in manifests:
                refurl: Optional[str] = None
                if project_path and manifest_spec.dependencies:
                    project_path_rel = resolve_relative(project_path)
                    git = Git(project_path_rel)
                    refurl = git.get_url()
                    if not refurl:
                        raise GitCloneMissingOriginError(project_path_rel)

                _LOGGER.debug("%r", manifest_spec)

                for spec in manifest_spec.dependencies:
                    dep_project = Project.from_spec(
                        manifest_spec, spec, level, refurl=refurl, resolve_url=self.resolve_url
                    )

                    # Update every path just once
                    if dep_project.path in done:
                        _LOGGER.debug("DUPLICATE %r", dep_project)
                        continue
                    done.append(dep_project.path)

                    if not group_filter(dep_project.path, dep_project.groups) or not project_filter(dep_project):
                        _LOGGER.debug("FILTERED OUT %r", dep_project)
                        continue

                    _LOGGER.debug("%r", dep_project)
                    projects.append(dep_project)

            if projects:
                yield tuple(projects)

            # See projects for manifests
            manifests.clear()
            level += 1
            for dep_project in projects:
                # Recursive?
                if not dep_project.recursive:
                    continue

                # Manifest?
                dep_project_path = self.workspace.get_project_path(dep_project)
                dep_manifest_path = dep_project_path / (find_manifest(dep_project_path) or dep_project.manifest_path)
                try:
                    dep_manifest_spec = self.manifest_format_manager.load(dep_manifest_path)
                except ManifestNotFoundError:
                    continue

                # Empty?
                if not dep_manifest_spec.dependencies:
                    continue

                dep_group_selects = group_selects_from_groups(dep_project.with_groups)
                dep_filter = create_filter(dep_group_selects)
                manifests.append((dep_project_path, dep_manifest_spec, dep_filter))

            projects.clear()


class ProjectIter:
    """
    Iterate over all :py:class:`gitws.Project` s.

    The iterator takes a :py:class:`gitws.Workspace` and the path to a manifest file (`manifest_path`)
    of the main project.
    The manifest is read (:py:class:`gitws.ManifestSpec`) and all dependencies are translated to
    :py:class:`gitws.Project` s, which are yielded.
    The manifest files of the dependencies are also read, translated to a :py:class:`gitws.Project` s
    and yielded likewise, until all manifest files and their dependencies are read.
    Dependencies which have been already yielded are not evaluated again.
    Means the first dependency (i.e. from the MAIN project) wins. Including the specified
    attributes (i.e. revision).

    Args:
        workspace: The current workspace
        manifest_path: Path to the manifest file **in the main project**.
        group_filters: Group Filters.

    Keyword Args:
        skip_main: Do not yield main project.
        resolve_url: Resolve relative URLs to absolute ones.

    Yields:
        :py:class:`gitws.Project`
    """

    def __init__(
        self,
        workspace: Workspace,
        manifest_format_manager: ManifestFormatManager,
        manifest_path: Path,
        group_filters: GroupFilters,
        filter_: Optional[ProjectFilterFunc] = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ):
        self.workspace: Workspace = workspace
        self.manifest_format_manager: ManifestFormatManager = manifest_format_manager
        self.manifest_path: Path = manifest_path
        self.group_filters: GroupFilters = group_filters
        self.filter_: Optional[ProjectFilterFunc] = filter_
        self.skip_main: bool = skip_main
        self.resolve_url: bool = resolve_url

    def __iter__(self) -> Iterator[Project]:
        for projects in ProjectLevelIter(
            workspace=self.workspace,
            manifest_format_manager=self.manifest_format_manager,
            manifest_path=self.manifest_path,
            group_filters=self.group_filters,
            filter_=self.filter_,
            skip_main=self.skip_main,
            resolve_url=self.resolve_url,
        ):
            yield from projects


def create_filter(group_selects: GroupSelects, default: bool = False) -> GroupFilterFunc:
    """
    Create Group Filter Function.

    Keyword Args:
        group_selects: Iterable with :py:class:`gitws.GroupSelect`.
        default: Default selection of all ``groups``.

    Filter projects based on their ``path`` and ``groups``.
    The filter has ``group_selects``, a specification which groups should be included or excluded.
    The default selection of these groups is controlled by ``default``.


    >>> group_filters = ('-@special', '+test', '+doc', '+feature@dep', '-doc')
    >>> group_selects = group_selects_from_filters(group_filters)
    >>> groupfilter = create_filter(group_selects)
    >>> groupfilter('sub', ())  # selected as there is no group
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
    >>> groupfilter('special', ())  # deselected, even without group
    False
    >>> groupfilter('special', ('foo', 'bar'))  # deselected
    False
    >>> groupfilter('special', ('test', 'bar'))  # deselected, but overwritten by '+test'
    True

    The same, but with ``default=True``:

    >>> groupfilter = create_filter(group_selects, default=True)
    >>> groupfilter('sub', ())  # selected as there is no group
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
    >>> groupfilter('special', ())  # deselected, even without group
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
                selects = {"": True}
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
            if groups:
                return default
            return True

    return filter_
