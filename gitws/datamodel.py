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
Central :any:`GitWS` Datamodel.

* :any:`Group`: Dependency Group. A string (i.e. 'test').
* :any:`GroupFilter`: Group Filter Specification. A string (i.e. '+test@path').
* :any:`GroupSelect`: Group Selection. A converted :any:`GroupFilter` as needed by :any:`GitWS`.
* :any:`ManifestSpec`: Manifest specification for the current project.
* :any:`Manifest`: Manifest as needed by :any:`GitWS` derived from :any:`ManifestSpec`.
* :any:`ProjectSpec`: Dependency Specification in :any:`ManifestSpec`.
* :any:`Project`: A Single Dependency as needed by :any:`GitWS` derived from :any:`ProjectSpec`.
* :any:`Remote`: Remote Alias in :any:`ManifestSpec`.
* :any:`Defaults`: Default Values in :any:`ManifestSpec`.
* :any:`AppConfigData`: :any:`GitWS` Configuration.
"""


import re
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Tuple

from pydantic import AfterValidator, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

from ._basemodel import BaseModel
from ._url import is_urlabs, urljoin, urlsub
from ._util import get_repr
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import NoAbsUrlError

_RE_GROUP = re.compile(r"\A[a-zA-Z0-9_][a-zA-Z0-9_\-]*\Z")

ProjectPath = str
"""Project Path."""

ProjectPaths = Tuple[ProjectPath, ...]


def _validate_name(name):
    """
    Validate Name.

    name is just a ``str`` for performance reasons. This function does the validation.
    """
    parts = PurePath(name).parts
    if ".." in parts:
        raise ValueError(f"Invalid name {name!r}")
    return name


def _validate_path(path):
    """
    Validate Path.

    path is just a ``str`` for performance reasons. This function does the validation.
    """
    parts = PurePath(path).parts
    if ".." in parts:
        raise ValueError(f"Invalid path {path!r}")
    return path


def _validate_group(group):
    """
    Validate Group.

    Group is just a ``str`` for performance reasons. This function does the validation.
    """
    mat = _RE_GROUP.match(group)
    if not mat:
        raise ValueError(f"Invalid group {group!r}")
    return group


Group = Annotated[str, AfterValidator(_validate_group)]
"""
Dependency Group.

A group is a name consisting of lower- and uppercase letters, numbers and underscore.
Dashes are allowed. Except the first sign.

Groups structure dependencies.
"""

Groups = Tuple[Group, ...]


_RE_GROUP_FILTER = re.compile(r"\A(?P<select>[\-\+])(?P<group>[a-zA-Z0-9_][a-zA-Z0-9_\-]*)?(@(?P<path>.+))?\Z")


def _validate_group_filter(group_filter):
    """
    Validate Group Filter.

    Group Filter are just a ``tuple`` of ``str`` for performance reasons. This function does the validation.
    """
    group_filter = str(group_filter)
    mat = _RE_GROUP_FILTER.match(group_filter)
    if not mat:
        raise ValueError(f"Invalid group filter {group_filter!r}")
    return group_filter


GroupFilter = Annotated[str, AfterValidator(_validate_group_filter)]
"""
Group Filter.

A group filter is a group name prefixed by '+' or '-', to select or deselect the group.
A group filter can have an optional path at the end.

Any :any:`GroupFilter` is later-on converted to a :any:`GroupSelect`.
"""

GroupFilters = Tuple[GroupFilter, ...]
"""
Groups Filter Specification from User.

Used by Config and Command Line Interface.
"""


class GroupSelect(BaseModel):
    """
    Group Selection.

    A group selection selects/deselects a specific group for a specific path.

    Keyword Args:
        select: Select (`True`) or Deselect (`False`)
        group: Group Name.
        path: Path.
    """

    model_config = ConfigDict(frozen=True)

    group: Optional[Group] = None
    """Group."""
    select: bool
    """Selected ('+') or not ('-')."""
    path: Optional[str] = None
    """Path."""

    @staticmethod
    def from_group(group: Group) -> "GroupSelect":
        """
        Create :any:`GroupSelect` from ``group``.

        >>> GroupSelect.from_group('test')
        GroupSelect(group='test', select=True)
        """
        return GroupSelect(group=group, select=True)

    @staticmethod
    def from_group_filter(group_filter: GroupFilter) -> "GroupSelect":
        """
        Create Group Selection from ``group_filter``.

        >>> GroupSelect.from_group_filter("+test")
        GroupSelect(group='test', select=True)
        >>> GroupSelect.from_group_filter("-test")
        GroupSelect(group='test', select=False)
        >>> GroupSelect.from_group_filter("-test@path")
        GroupSelect(group='test', select=False, path='path')
        >>> GroupSelect.from_group_filter("-@path")
        GroupSelect(select=False, path='path')
        >>> GroupSelect.from_group_filter("te-st")
        Traceback (most recent call last):
            ...
        ValueError: Invalid group selection 'te-st'
        """
        mat = _RE_GROUP_FILTER.match(group_filter)
        if not mat:
            raise ValueError(f"Invalid group selection {group_filter!r}")
        data = mat.groupdict()
        data["select"] = data["select"] == "+"
        return GroupSelect(**data)

    def __str__(self):
        select = "+" if self.select else "-"
        path = f"@{self.path}" if self.path else ""
        return f"{select}{self.group}{path}"


GroupSelects = Tuple[GroupSelect, ...]
"""Group Selects."""


def group_selects_from_groups(groups: Groups) -> GroupSelects:
    """Create :any:`GroupSelects` from `GroupFilters`."""
    return tuple(GroupSelect.from_group(group) for group in groups)


def group_selects_from_filters(group_filters: GroupFilters) -> GroupSelects:
    """Create :any:`GroupSelects` from `GroupFilters`."""
    return tuple(GroupSelect.from_group_filter(group_filter) for group_filter in group_filters)


class Remote(BaseModel):
    """
    Remote Alias - Remote URL Helper.

    Args:
        name: Remote Name

    Keyword Args:
        url_base: Base URL. Optional.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    name: str
    """The Name of the Remote. Must be unique within Manifest."""

    url_base: str = Field(None, alias="url-base")
    """URL to a directory of repositories."""


class Defaults(BaseModel):
    """
    Default Values.

    These default values are used, if a :any:`ProjectSpec` does not specify them.

    Keyword Args:
        remote: Remote Name.
        revision: Revision. Tag or Branch. SHA does not make sense here.
        groups: Dependency Groups.
        with_groups: Group Selection for refered projects.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True, arbitrary_types_allowed=True)

    remote: Optional[str] = None
    """Remote name if not specified by the dependency. The remote must have been defined previously."""

    revision: Optional[str] = None
    """The revision if not specified by the dependency. Tag or Branch. SHA does not make sense here."""

    groups: Optional[Groups] = ()
    """The ``groups`` attribute if not specified by the dependency."""

    with_groups: Optional[Groups] = Field((), alias="with-groups")
    """The ``with_groups`` attribute if not specified by the dependency."""

    submodules: bool = True
    """Initialize and Update `git submodules`. `True` by default."""


class FileRef(BaseModel):
    """
    File Reference Specification.

    The main project and first level dependencies might specify symbolic-links or files-to-copy.

    Args:
        src: Source - path relative to the project directory.
        dest: Destination - relative path to the workspace directory.
    """

    model_config = ConfigDict(frozen=True)

    src: str
    """Source - path relative to the project directory."""

    dest: str
    """Destination - relative path to the workspace directory."""


FileRefs = Tuple[FileRef, ...]


class MainFileRef(FileRef):
    """
    Main Project File Reference.

    Args:
        src: Source - path relative to the project directory.
        dest: Destination - relative path to the workspace directory.

    Keyword Args:
        groups: Groups
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    groups: Groups = ()
    """``groups`` specification."""


MainFileRefs = Tuple[MainFileRef, ...]


class WorkspaceFileRef(BaseModel):
    """
    Current File Reference with Workspace.

    Args:
        project_path - Project Path.
        src: Source - path relative to the project directory.
        dest: Destination - relative path to the workspace directory.

    Keyword Args:
        hash_: Source File Hash for Copied Files.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    type_: str
    """File Type."""

    project_path: str
    """Project Path."""

    src: str
    """Source - path relative to `project_path`."""

    dest: str
    """Destination - relative path to the workspace directory."""

    hash_: Optional[int] = None
    """Hash - Source File Hash for Copied Files."""


WorkspaceFileRefs = List[WorkspaceFileRef]


class Project(BaseModel):
    """
    Project.

    A project describes a dependency.

    Args:
        name: Name.
        path: Project Filesystem Path. Relative to Workspace Root Directory.

    Keyword Args:
        level: Dependency Tree Level.
        url: URL. Assembled from ``remote`` s ``url_base``, ``sub_url`` and/or ``name``.
        revision: Revision to be checked out. Tag, branch or SHA.
        manifest_path: Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default.
        groups: Dependency Groups.
        with_groups: Group Selection for refered project.
        submodules: initialize and update `git submodules`
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
        recursive: integrate dependencies of this dependency
        is_main: Project is Main Project.

    The :any:`ProjectSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Project` is the resolved version of :any:`ProjectSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    :any:`Project.from_spec()` resolves a :any:`ProjectSpec` into a :any:`Project`.
    :any:`ProjectSpec.from_project()` does the reverse.

    .. note::
        :any:`Project.from_spec()` resolves some attributes irreversible.
        So ``Project.from_spec(ProjectSpec.from_project())`` will not
        return the original project.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)
    name: Annotated[str, AfterValidator(_validate_name)]
    """Dependency Name."""

    path: Annotated[str, AfterValidator(_validate_path)]
    """Dependency Path. ``name`` will be used as default."""

    level: Optional[int] = None
    """Dependency Tree Level."""

    url: Optional[str] = None
    """URL. Assembled from ``remote`` s ``url_base``, ``sub_url`` and/or ``name``."""

    revision: Optional[str] = None
    """Revision to be checked out. Tag, branch or SHA."""

    manifest_path: str = str(MANIFEST_PATH_DEFAULT)
    """Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default."""

    groups: Groups = ()
    """Dependency Groups."""

    with_groups: Groups = Field((), alias="with-groups")
    """Group Selection for referred project."""

    submodules: bool = True
    """Initialize and Update `git submodules`."""

    linkfiles: FileRefs = ()
    """Symbolic Links To Be Created In The workspace."""

    copyfiles: FileRefs = ()
    """Files To Be Created In The Workspace."""

    recursive: bool = True
    """Integrate Dependencies of this dependency."""

    is_main: bool = False
    """Project is the main project."""

    @property
    def info(self):
        """
        `repr`-like info string but more condensed.

        >>> Project(name='name', path='name').info
        'name'
        >>> Project(name='name', path='path').info
        "name (path='path')"
        >>> Project(name='name', path='name', revision='main').info
        "name (revision='main')"
        >>> Project(name='name', path='name', groups=('test', 'doc')).info
        "name (groups='test,doc')"
        """
        options = get_repr(
            kwargs=(
                ("revision", self.revision, None),
                ("path", str(self.path), self.name),
                ("groups", ",".join(self.groups), ""),
                ("submodules", self.submodules, True),
            )
        )
        if self.is_main:
            options = f"MAIN {options}" if options else "MAIN"
        if options:
            return f"{self.name} ({options})"
        return self.name

    @staticmethod
    def from_spec(
        manifest_spec: "ManifestSpec",
        spec: "ProjectSpec",
        level: int,
        refurl: Optional[str] = None,
        resolve_url: bool = False,
    ) -> "Project":
        """
        Create :any:`Project` from ``manifest_spec`` and ``spec``.

        Args:
            manifest_spec: Manifest Specification.
            spec: Base project to be resolved.
            level: Dependency tree level.

        Keyword Args:
            refurl: Remote URL of the ``manifest_spec``.
            resolve_url: Resolve URLs to absolute ones.

        Raises:
            NoAbsUrlError: On ``resolve_url=True`` if ``refurl`` is ``None`` and project uses a relative URL.

        :any:`Project.from_spec()` resolves a :any:`ProjectSpec` into a :any:`Project`.
        :any:`ProjectSpec.from_project()` does the reverse.
        """
        defaults = manifest_spec.defaults
        remotes = manifest_spec.remotes
        project_groups = spec.groups or defaults.groups
        project_with_groups = spec.with_groups or defaults.with_groups
        submodules = spec.submodules if spec.submodules is not None else defaults.submodules
        # URL
        url = spec.url
        if not url:
            # URL assembly
            project_remote = spec.remote or defaults.remote
            project_sub_url = spec.sub_url or urlsub(refurl, spec.name)
            if project_remote:
                for remote in remotes:
                    if remote.name == project_remote:
                        url = f"{remote.url_base}/{project_sub_url}"
                        break
                else:
                    raise ValueError(f"Unknown remote {spec.remote} for project {spec.name}")
            else:
                url = f"../{project_sub_url}"

        # Resolve relative URLs.
        if resolve_url and not is_urlabs(url):
            if not refurl:
                raise NoAbsUrlError(spec.name)
            url = urljoin(refurl, url)

        # Create
        return Project(
            name=spec.name,
            level=level,
            path=spec.path or spec.name,
            url=url,
            revision=spec.revision or defaults.revision,
            manifest_path=spec.manifest_path,
            groups=project_groups,
            with_groups=project_with_groups,
            submodules=submodules,
            linkfiles=spec.linkfiles,
            copyfiles=spec.copyfiles,
            recursive=spec.recursive,
        )


class ProjectSpec(BaseModel):
    """
    Project Dependency Specification.

    A project specifies the reference to a repository.

    Args:
        name: Name.

    Keyword Args:
        remote: Remote Alias - Remote URL Helper
        sub_url: URL relative to :any:`Remote.url_base`.
        url: URL
        revision: Revision
        path: Project Filesystem Path. Relative to Workspace Root Directory.
        manifest_path: Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default.
        groups: Dependency Groups.
        with_groups: Group Selection for refered project.
        submodules: initialize and update `git submodules`
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
        recursive: integrate dependencies of this dependency

    Some parameters are restricted:

    * ``remote`` and ``url`` are mutually exclusive.
    * ``url`` and ``sub-url`` are likewise mutually exclusive
    * ``sub-url`` requires a ``remote``.

    The :any:`ProjectSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Project` is the resolved version of :any:`ProjectSpec` with all calculated information needed by
    :any:`GitWS` to operate.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    name: Annotated[str, AfterValidator(_validate_name)]
    """Dependency Name."""

    remote: Optional[str] = None
    """Remote Alias Name. The ``remote`` must have been defined previously."""

    sub_url: Optional[str] = Field(None, alias="sub-url")
    """Relative URL to ``remote`` s ``url_base`` OR the URL of the manifest file."""

    url: Optional[str] = None
    """Absolute URL."""

    revision: Optional[str] = None
    """Revision to be checked out."""

    path: Annotated[Optional[str], AfterValidator(_validate_path)] = None
    """Path within workspace. ``name`` will be used as default."""

    manifest_path: Optional[str] = Field(str(MANIFEST_PATH_DEFAULT), alias="manifest-path")
    """Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default."""

    groups: Groups = ()
    """Dependency Groups."""

    with_groups: Groups = Field((), alias="with-groups")
    """Group Selection for refered project."""

    submodules: Optional[bool] = None
    """Initialize and Update `git submodules`."""

    linkfiles: FileRefs = ()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: FileRefs = ()
    """Files To Be Created In The Workspace."""

    recursive: bool = True
    """Integrate Dependencies of this dependency."""

    @model_validator(mode="after")
    def _remote_or_url(self):
        remote = self.remote
        sub_url = self.sub_url
        url = self.url
        if remote and url:
            raise ValueError("'remote' and 'url' are mutually exclusive")
        if url and sub_url:
            raise ValueError("'url' and 'sub-url' are mutually exclusive")
        if sub_url and not remote:
            raise ValueError("'sub-url' requires 'remote'")
        return self

    @staticmethod
    def from_project(project: Project) -> "ProjectSpec":
        """
        Create :any:`ProjectSpec` from ``project``.

        Args:
            project: The source :any:`Project`.

        .. note::
            :any:`Project.from_spec()` resolves some attributes irreversible.
            So ``Project.from_spec(ProjectSpec.from_project())`` will not
            return the original project.
        """
        return ProjectSpec(
            name=project.name,
            path=project.path,
            url=project.url,
            revision=project.revision,
            manifest_path=project.manifest_path,
            groups=project.groups,
            with_groups=project.with_groups,
            submodules=project.submodules,
            linkfiles=project.linkfiles,
            copyfiles=project.copyfiles,
            recursive=project.recursive,
        )


class Manifest(BaseModel):
    """
    The Manifest.

    A manifest describes the current project and its dependencies.

    Keyword Args:
        group_filters: Group Filtering.
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
        dependencies: Dependency Projects.
        path: Filesystem Path. Relative to Workspace Root Directory.

    The :any:`ManifestSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Manifest` is the resolved version of :any:`ManifestSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    :any:`Manifest.from_spec()` resolves a :any:`ManifestSpec` into a :any:`Manifest`.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    group_filters: GroupFilters = Field((), alias="group-filters")
    """Default Group Selection and Deselection."""

    linkfiles: MainFileRefs = ()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: MainFileRefs = ()
    """Files To Be Created In The Workspace."""

    dependencies: Tuple[Project, ...] = ()
    """Dependencies - Other Projects To Be Cloned In The Workspace."""

    path: Optional[str] = None
    """Path to the manifest file, relative to project path."""

    @staticmethod
    def from_spec(
        spec: "ManifestSpec", path: Optional[str] = None, refurl: Optional[str] = None, resolve_url: bool = False
    ) -> "Manifest":
        """
        Create :any:`Manifest` from :any:`ManifestSpec`.

        Args:
            spec: The source :any:`ManifestSpec`.

        Keyword Args:
            path: File path of the ``spec``.
            refurl: URL of the repository containing ``spec``.
            resolve_url: Convert relative to absolute URLs. Requires ``refurl``.

        Raises:
            NoAbsUrlError: On ``resolve_url=True`` if ``refurl`` is ``None`` and project uses a relative URL.
        """
        dependencies = [
            Project.from_spec(spec, project_spec, 1, refurl=refurl, resolve_url=resolve_url)
            for project_spec in spec.dependencies
        ]
        return Manifest(
            group_filters=spec.group_filters,
            linkfiles=spec.linkfiles,
            copyfiles=spec.copyfiles,
            dependencies=dependencies,
            path=path,
        )


class ManifestSpec(BaseModel):
    """
    ManifestSpec.

    A manifest describes the current project and its dependencies.

    The :any:`ManifestSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Manifest` is the resolved version of :any:`ManifestSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    Keyword Args:
        version: Version String. Currently 1.0.
        remotes: Remote Aliases.
        group_filters: Group Filtering.
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
        defaults: Default settings.
        dependencies: Dependency Projects.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True, extra="allow")

    version: str = Field(default="1.0")
    """
    Manifest Version Identifier.

    Actual Version: ``1.0``.
    """

    group_filters: GroupFilters = Field((), alias="group-filters")
    """Default Group Selection and Deselection."""

    linkfiles: MainFileRefs = ()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: MainFileRefs = ()
    """Files To Be Created In The Workspace."""

    remotes: Tuple[Remote, ...] = ()
    """Remotes - Helpers to Simplify URL Handling."""

    defaults: Defaults = Defaults()
    """Default Values."""

    dependencies: Tuple[ProjectSpec, ...] = ()
    """Dependencies - Other Projects To Be Cloned In The Workspace."""

    @model_validator(mode="after")
    def _validate_unique_remotes(self):
        # unique remote names
        names = set()
        for remote in self.remotes:
            name = remote.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Remote name {name!r} is used more than once")
        return self

    @model_validator(mode="after")
    def _validate_unique_deps(self):
        # unique dependency names
        names = set()
        for dep in self.dependencies:
            name = dep.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Dependency name {name!r} is used more than once")
        return self


class AppConfigData(BaseSettings):
    """
    Configuration data of the application.

    This class holds the concrete configuration values of the application.
    The following values are defined:
    """

    model_config = SettingsConfigDict(extra="allow")

    manifest_path: Optional[str] = Field(
        default=None, description="The path (relative to the project's root folder) to the manifest file."
    )
    """
    The path of the manifest file within a repository.

    If this is not defined, the default is ``git-ws.toml``.

    This option can be overridden by specifying the ``GIT_WS_MANIFEST_PATH`` environment variable.
    """

    color_ui: Optional[bool] = Field(
        default=None, description="If set to true, the output the tool generates will be colored."
    )
    """
    Defines if outputs by the tool shall be colored.

    If this is not defined, output will be colored by default.

    This option can be overridden by specifying the ``GIT_WS_COLOR_UI`` environment variable.
    """

    group_filters: Optional[GroupFilters] = Field(default=None, description="The groups to operate on.")
    """
    The groups to operate on.

    This is a filter for groups to operate on during workspace actions.

    This option can be overridden by specifying the ``GIT_WS_GROUP_FILTERS`` environment variable.
    """

    clone_cache: Optional[Path] = Field(default=None, description="Local Cache for Git Clones.")
    """
    Clone Cache.

    Initial cloning all dependencies takes a while. This sums up if done often (i.e. in CI/CD).
    This local filesystem cache directory will be used, to re-use already cloned data.

    This option can be overridden by specifying the ``GIT_WS_CLONE_CACHE`` environment variable.
    """

    depth: Optional[int] = Field(default=None, description="Default Clone Depth for New Clones")
    """
    Default Clone Depth.

    New clones are created with the given depth.
    0 deactivates shallow cloning.
    """

    @staticmethod
    def defaults() -> Dict[str, Any]:
        """
        As all configuration options must be optional, this option provides the default values.

        >>> for item in AppConfigData.defaults().items(): print(item)
        ('color_ui', True)
        ('manifest_path', 'git-ws.toml')
        """
        return {
            "color_ui": True,
            "manifest_path": str(MANIFEST_PATH_DEFAULT),
        }
