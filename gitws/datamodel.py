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
* :any:`Groups`: Tuple of :any:`Group` instances.
* :any:`GroupFilter`: Group Filter Specification. A string (i.e. '+test@path').
* :any:`GroupFilters`: Tuple of :any:`GroupFilter` instances.
* :any:`GroupSelect`: Group Selection. A converted :any:`GroupFilter` as needed by :any:`GitWS`.
* :any:`GroupSelects`: Tuple of :any:`GroupSelect` instances.
* :any:`ManifestSpec`: Manifest specification for the actual project.
* :any:`Manifest`: Manifest as needed by :any:`GitWS` derived from :any:`ManifestSpec`.
* :any:`ProjectSpec`: Dependency Specification in :any:`ManifestSpec`.
* :any:`Project`: A Single Dependency as needed by :any:`GitWS` derived from :any:`ProjectSpec`.
* :any:`Remote`: Remote Alias in :any:`ManifestSpec`.
* :any:`Defaults`: Default Values in :any:`ManifestSpec`.
* :any:`AppConfigData`: :any:`GitWS` Configuration.
"""

# pylint: disable=too-many-lines

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tomlkit
from pydantic import BaseSettings, Extra, Field, root_validator, validator

from ._basemodel import BaseModel
from ._url import is_urlabs, urljoin, urlsub
from ._util import add_comment, add_info, as_dict, get_repr, resolve_relative
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestError, ManifestNotFoundError, NoAbsUrlError

_RE_GROUP = re.compile(r"\A[a-zA-Z0-9_][a-zA-Z0-9_\-]*\Z")

ProjectPaths = Tuple[
    str,
]

Group = str
"""
Dependency Group.

A group is a name consisting of lower- and uppercase letters, numbers and underscore.
Dashes are allowed. Except the first sign.

Groups structure dependencies.
"""


def validate_group(group):
    """
    Validate Group.

    Group is just a ``str`` for performance reasons. This function does the validation.
    """
    mat = _RE_GROUP.match(group)
    if not mat:
        raise ValueError(f"Invalid group {group!r}")


class Groups(tuple):

    """Groups."""

    @staticmethod
    def validate(groups):
        """
        Validate Groups.

        Groups are just a ``tuple`` of ``str`` for performance reasons. This function does the validation.
        """
        for group in groups:
            validate_group(group)
        return groups


_RE_GROUP_FILTER = re.compile(r"\A(?P<select>[\-\+])(?P<group>[a-zA-Z0-9_][a-zA-Z0-9_\-]*)?(@(?P<path>.+))?\Z")

GroupFilter = str
"""
Group Filter.

A group filter is a group name prefixed by '+' or '-', to select or deselect the group.
A group filter can have an optional path at the end.

Any :any:`GroupFilter` is later-on converted to a :any:`GroupSelect`.
"""


def validate_group_filter(group_filter):
    """
    Groups Filter.

    Group Filters are just a ``tuple`` of ``str`` for performance reasons. This function does the validation.
    """
    mat = _RE_GROUP_FILTER.match(group_filter)
    if not mat:
        raise ValueError(f"Invalid group filter {group_filter!r}")


class GroupFilters(tuple):
    """
    Groups Filter Specification from User.

    Used by Config and Command Line Interface.
    """

    @staticmethod
    def validate(group_filters):
        """
        Check Groups Filter.

        Group Filters are just a ``tuple`` of ``str`` for performance reasons. This function does the validation.
        """
        for group_filter in group_filters:
            validate_group_filter(group_filter)
        return group_filters


class GroupSelect(BaseModel):

    """
    Group Selection.

    A group selection selects/deselects a specific group for a specific path.

    Keyword Args:
        select: Select (`True`) or Deselect (`False`)
        group: Group Name.
        path: Path.
    """

    group: Optional[Group] = None
    """Group."""
    select: bool
    """Selected ('+') or not ('-')."""
    path: Optional[str] = None
    """Path."""

    @staticmethod
    def from_group_filter(group_filter) -> "GroupSelect":
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


class GroupSelects(tuple):

    """Collection of :any:`GroupSelect`."""

    @staticmethod
    def from_group_filters(group_filters: Optional[GroupFilters] = None) -> "GroupSelects":
        """
        Create :any:`GroupSelects` from ``group_filters``.

        >>> GroupSelects.from_group_filters()
        ()
        >>> GroupSelects.from_group_filters(('', ))
        ()
        >>> GroupSelects.from_group_filters(('+test', ))
        (GroupSelect(group='test', select=True),)
        >>> GroupSelects.from_group_filters(('+test', '-doc'))
        (GroupSelect(group='test', select=True), GroupSelect(group='doc', select=False))
        """
        group_filters = group_filters or GroupFilters()
        items = [item.strip() for item in group_filters]
        return GroupSelects(GroupSelect.from_group_filter(item) for item in items if item)

    @staticmethod
    def from_groups(groups: Optional[Groups] = None) -> "GroupSelects":
        """
        Create :any:`GroupSelects` from ``group_filters``.

        >>> GroupSelects.from_groups()
        ()
        >>> GroupSelects.from_groups(('', ))
        ()
        >>> GroupSelects.from_groups(('test', ))
        (GroupSelect(group='test', select=True),)
        >>> GroupSelects.from_groups(('test', 'doc'))
        (GroupSelect(group='test', select=True), GroupSelect(group='doc', select=True))
        """
        groups = groups or Groups()
        items = [item.strip() for item in groups]
        return GroupSelects(GroupSelect(group=item, select=True) for item in items if item)


class Remote(BaseModel, allow_population_by_field_name=True):
    """
    Remote Alias - Remote URL Helper.

    Args:
        name: Remote Name

    Keyword Args:
        url_base: Base URL. Optional.
    """

    name: str
    """The Name of the Remote. Must be unique within Manifest."""

    url_base: str = Field(None, alias="url-base")
    """URL to a directory of repositories."""


class Defaults(BaseModel, allow_population_by_field_name=True):
    """
    Default Values.

    These default values are used, if a :any:`ProjectSpec` does not specify them.

    Keyword Args:
        remote: Remote Name.
        revision: Revision. Tag or Branch. SHA does not make sense here.
        groups: Dependency Groups.
        with_groups: Group Selection for refered projects.
    """

    remote: Optional[str] = None
    """Remote name if not specified by the dependency. The remote must have been defined previously."""

    revision: Optional[str] = None
    """The revision if not specified by the dependency. Tag or Branch. SHA does not make sense here."""

    groups: Optional[Groups] = Groups()
    """The ``groups`` attribute if not specified by the dependency."""

    with_groups: Optional[Groups] = Field(Groups(), alias="with-groups")
    """The ``with_groups`` attribute if not specified by the dependency."""

    submodules: bool = True
    """Initialize and Update `git submodules`. `True` by default."""

    @validator("groups", allow_reuse=True)
    def _groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)

    @validator("with_groups", allow_reuse=True)
    def _with_groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)


class FileRef(BaseModel):
    """
    File Reference (Symbolic Link or File to Copy).

    File Reference to Workspace from Project.

    Keyword Args:
        src: Source - relative path to the project directory.
        dest: Destination - relative path to the workspace directory.
    """

    src: str
    """Source - relative path to the project directory."""

    dest: str
    """Destination - relative path to the workspace directory."""


FileRefs = Tuple[FileRef, ...]
ProjectFileRefs = Dict[str, FileRefs]
FileRefsMutable = List[FileRef]
ProjectFileRefsMutable = Dict[str, FileRefsMutable]


class Project(BaseModel, allow_population_by_field_name=True):

    """
    Project.

    A project describes a dependency.

    Args:
        name: Name.
        path: Project Filesystem Path. Relative to Workspace Root Directory.

    Keyword Args:
        url: URL. Assembled from ``remote`` s ``url_base``, ``sub_url`` and/or ``name``.
        revision: Revision to be checked out. Tag, branch or SHA.
        manifest_path: Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default.
        groups: Dependency Groups.
        with_groups: Group Selection for refered project.
        submodules: initialize and update `git submodules`
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
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

    name: str
    """Dependency Name."""

    path: str
    """Dependency Path. ``name`` will be used as default."""

    url: Optional[str] = None
    """URL. Assembled from ``remote`` s ``url_base``, ``sub_url`` and/or ``name``."""

    revision: Optional[str] = None
    """Revision to be checked out. Tag, branch or SHA."""

    manifest_path: str = str(MANIFEST_PATH_DEFAULT)
    """Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default."""

    groups: Groups = Groups()
    """Dependency Groups."""

    with_groups: Groups = Field(Groups(), alias="with-groups")
    """Group Selection for referred project."""

    submodules: bool = True
    """Initialize and Update `git submodules`."""

    linkfiles: Tuple[FileRef, ...] = tuple()
    """Symbolic Links To Be Created In The workspace."""

    copyfiles: Tuple[FileRef, ...] = tuple()
    """Files To Be Created In The Workspace."""

    is_main: bool = False
    """Project is the main project."""

    @validator("groups", allow_reuse=True)
    def _groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)

    @validator("with_groups", allow_reuse=True)
    def _with_groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)

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
        manifest_spec: "ManifestSpec", spec: "ProjectSpec", refurl: Optional[str] = None, resolve_url: bool = False
    ) -> "Project":
        """
        Create :any:`Project` from ``manifest_spec`` and ``spec``.

        Args:
            manifest_spec: Manifest Specification.
            spec: Base project to be resolved.

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
            path=spec.path or spec.name,
            url=url,
            revision=spec.revision or defaults.revision,
            manifest_path=spec.manifest_path,
            groups=project_groups,
            with_groups=project_with_groups,
            submodules=submodules,
            linkfiles=spec.linkfiles,
            copyfiles=spec.copyfiles,
        )


class ProjectSpec(BaseModel, allow_population_by_field_name=True):
    """
    Project Dependency Specification

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

    Some parameters are restricted:

    * ``remote`` and ``url`` are mutually exclusive.
    * ``url`` and ``sub-url`` are likewise mutually exclusive
    * ``sub-url`` requires a ``remote``.

    The :any:`ProjectSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Project` is the resolved version of :any:`ProjectSpec` with all calculated information needed by
    :any:`GitWS` to operate.
    """

    name: str
    """Dependency Name."""

    remote: Optional[str] = None
    """Remote Alias Name. The ``remote`` must have been defined previously."""

    sub_url: Optional[str] = Field(None, alias="sub-url")
    """Relative URL to ``remote`` s ``url_base`` OR the URL of the manifest file."""

    url: Optional[str] = None
    """Absolute URL."""

    revision: Optional[str] = None
    """Revision to be checked out."""

    path: Optional[str] = None
    """Path within workspace. ``name`` will be used as default."""

    manifest_path: Optional[str] = Field(str(MANIFEST_PATH_DEFAULT), alias="manifest-path")
    """Path to the manifest file. Relative to ``path`` of project. ``git-ws.toml`` by default."""

    groups: Groups = Groups()
    """Dependency Groups."""

    with_groups: Groups = Field(Groups(), alias="with-groups")
    """Group Selection for refered project."""

    submodules: Optional[bool] = None
    """Initialize and Update `git submodules`."""

    linkfiles: Tuple[FileRef, ...] = tuple()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: Tuple[FileRef, ...] = tuple()
    """Files To Be Created In The Workspace."""

    @root_validator(allow_reuse=True)
    def _remote_or_url(cls, values):
        # pylint: disable=no-self-argument
        remote = values.get("remote", None)
        sub_url = values.get("sub_url", None)
        url = values.get("url", None)
        if remote and url:
            raise ValueError("'remote' and 'url' are mutually exclusive")
        if url and sub_url:
            raise ValueError("'url' and 'sub-url' are mutually exclusive")
        if sub_url and not remote:
            raise ValueError("'sub-url' requires 'remote'")
        return values

    @validator("groups", allow_reuse=True)
    def _groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)

    @validator("with_groups", allow_reuse=True)
    def _with_groups(cls, values):
        # pylint: disable=no-self-argument
        return Groups.validate(values)

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
        )


class Manifest(BaseModel, extra=Extra.allow, allow_population_by_field_name=True):

    """
    The Manifest.

    A manifest describes the actual project and its dependencies.

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

    group_filters: GroupFilters = Field(GroupFilters(), alias="group-filters")
    """Default Group Selection and Deselection."""

    linkfiles: Tuple[FileRef, ...] = tuple()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: Tuple[FileRef, ...] = tuple()
    """Files To Be Created In The Workspace."""

    dependencies: Tuple[Project, ...] = tuple()
    """Dependencies - Other Projects To Be Cloned In The Workspace."""

    path: Optional[str] = None
    """Path to the manifest file, relative to project path."""

    @validator("group_filters", allow_reuse=True)
    def _group_filters(cls, values):
        # pylint: disable=no-self-argument
        return GroupFilters.validate(values)

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
            Project.from_spec(spec, project_spec, refurl=refurl, resolve_url=resolve_url)
            for project_spec in spec.dependencies
        ]
        return Manifest(
            group_filters=spec.group_filters,
            linkfiles=spec.linkfiles,
            copyfiles=spec.copyfiles,
            dependencies=dependencies,
            path=path,
        )


class ManifestSpec(BaseModel, allow_population_by_field_name=True):

    """
    ManifestSpec.

    A manifest describes the actual project and its dependencies.

    The :any:`ManifestSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Manifest` is the resolved version of :any:`ManifestSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    Keyword Args:
        version: Version String. Actually 1.0.
        remotes: Remote Aliases.
        group_filters: Group Filtering.
        linkfiles: symbolic links to be created in the workspace
        copyfiles: files to be created in the workspace
        defaults: Default settings.
        dependencies: Dependency Projects.
    """

    version: str = Field(default="1.0")
    """
    Manifest Version Identifier.

    Actual Version: ``1.0``.
    """

    group_filters: GroupFilters = Field(GroupFilters(), alias="group-filters")
    """Default Group Selection and Deselection."""

    linkfiles: Tuple[FileRef, ...] = tuple()
    """Symbolic Links To Be Created In The Workspace."""

    copyfiles: Tuple[FileRef, ...] = tuple()
    """Files To Be Created In The Workspace."""

    remotes: Tuple[Remote, ...] = tuple()
    """Remotes - Helpers to Simplify URL Handling."""

    defaults: Defaults = Defaults()
    """Default Values."""

    dependencies: Tuple[ProjectSpec, ...] = tuple()
    """Dependencies - Other Projects To Be Cloned In The Workspace."""

    @root_validator(allow_reuse=True)
    def _remotes_unique(cls, values):
        # pylint: disable=no-self-argument
        names = set()
        for remote in values.get("remotes", None) or []:
            name = remote.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Remote name {name!r} is used more than once")
        return values

    @root_validator(allow_reuse=True)
    def _deps_unique(cls, values):
        # pylint: disable=no-self-argument
        names = set()
        for dep in values.get("dependencies", None) or []:
            name = dep.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Dependency name {name!r} is used more than once")
        return values

    @validator("group_filters", allow_reuse=True)
    def _group_filters(cls, values):
        # pylint: disable=no-self-argument
        return GroupFilters.validate(values)

    @classmethod
    def load(cls, path: Path) -> "ManifestSpec":
        """
        Load :any:`ManifestSpec` from ``path``.

        The file referenced by ``path`` must be a TOML file according to the manifest scheme.

        Raises:
            ManifestNotFoundError: if file is not found
            ManifestError: On syntax or data scheme errors.
        """
        try:
            content = path.read_text()
        except FileNotFoundError:
            raise ManifestNotFoundError(resolve_relative(path)) from None
        try:
            doc = tomlkit.parse(content)
            data = dict(doc)
            return cls(**data)
        except Exception as exc:
            raise ManifestError(resolve_relative(path), str(exc)) from None

    def dump(
        self, doc: Optional[tomlkit.TOMLDocument] = None, path: Optional[Path] = None, minimal: bool = False
    ) -> str:
        """
        Return :any:`ManifestSpec` as string.

        The output will include an inline documentation of all available options.
        If ``doc`` or ``path`` are specified, any additional attributes and comments are **kept**.

        Keyword Args:
            doc: Existing document to be updated.
            path: Path to possibly existing document.
            minimal: Skip unset

        >>> print(ManifestSpec(defaults=Defaults(revision='main'), dependencies=(ProjectSpec(name='mylib'),)).dump())
        version = "1.0"
        ##
        ## Git Workspace's Manifest. Please see the documentation at:
        ##
        ## https://git-ws.readthedocs.io/en/latest/manual/manifest.html
        ##
        <BLANKLINE>
        <BLANKLINE>
        # group-filters = ["-doc", "-feature@path"]
        group-filters = []
        <BLANKLINE>
        <BLANKLINE>
        # [[remotes]]
        # name = "myremote"
        # url-base = "https://github.com/myuser"
        <BLANKLINE>
        <BLANKLINE>
        [defaults]
        revision = "main"
        <BLANKLINE>
        # remote = "myserver"
        # revision = "main"
        # groups = ["test"]
        # with-groups = ["doc"]
        <BLANKLINE>
        <BLANKLINE>
        ## A full flavored dependency using a 'remote':
        # [[dependencies]]
        # name = "myname"
        # remote = "remote"
        # sub-url = "my.git"
        # revision = "main"
        # path = "mydir"
        # groups = ["group"]
        #
        # [[dependencies.linkfiles]]
        # src = "file0-in-mydir.txt"
        # dest = "link0-in-workspace.txt"
        #
        # [[dependencies.linkfiles]]
        # src = "file1-in-mydir.txt"
        # dest = "link1-in-workspace.txt"
        #
        # [[dependencies.copyfiles]]
        # src = "file0-in-mydir.txt"
        # dest = "file0-in-workspace.txt"
        #
        # [[dependencies.copyfiles]]
        # src = "file1-in-mydir.txt"
        # dest = "file1-in-workspace.txt"
        <BLANKLINE>
        ## A full flavored dependency using a 'url':
        # [[dependencies]]
        # name = "myname"
        # url = "https://github.com/myuser/my.git"
        # revision = "main"
        # path = "mydir"
        # groups = ["group"]
        #
        # [[dependencies.linkfiles]]
        # src = "file0-in-mydir.txt"
        # dest = "link0-in-workspace.txt"
        #
        # [[dependencies.linkfiles]]
        # src = "file1-in-mydir.txt"
        # dest = "link1-in-workspace.txt"
        #
        # [[dependencies.copyfiles]]
        # src = "file0-in-mydir.txt"
        # dest = "file0-in-workspace.txt"
        #
        # [[dependencies.copyfiles]]
        # src = "file1-in-mydir.txt"
        # dest = "file1-in-workspace.txt"
        <BLANKLINE>
        ## A minimal dependency:
        # [[dependencies]]
        # name = "my"
        [[dependencies]]
        name = "mylib"
        <BLANKLINE>
        <BLANKLINE>
        # [[linkfiles]]
        # src = "file-in-main-clone.txt"
        # dest = "link-in-workspace.txt"
        <BLANKLINE>
        <BLANKLINE>
        # [[copyfiles]]
        # src = "file-in-main-clone.txt"
        # dest = "file-in-workspace.txt"
        <BLANKLINE>
        """
        assert not doc or not path, "'doc' and 'path' are mutually exclusive."
        if doc is None:
            if path and path.exists():
                doc = tomlkit.parse(path.read_text())
            else:
                doc = self._create()
        if minimal:
            data = as_dict(self)
        else:
            data = {
                "version": ManifestSpec().version,
                "remotes": tomlkit.aot(),
                "group-filters": tuple(),
                "defaults": {},
                "dependencies": tomlkit.aot(),
                "linkfiles": tomlkit.aot(),
                "copyfiles": tomlkit.aot(),
            }
            data.update(as_dict(self))
        for key, value in data.items():
            doc[key] = value
        return tomlkit.dumps(doc)

    def save(self, path: Path, update=True):
        """
        Save :any:`ManifestSpec` at ``path``.

        The file will include an inline documentation of all available options.

        Keyword Args:
            update: Additional attributes and comments added by the user are **kept**.
                    Otherwise the file is just overwritten.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        if update:
            path.write_text(self.dump(path=path))
        else:
            path.write_text(self.dump())

    @classmethod
    def upgrade(cls, path: Path):
        """Upgrade :any:`ManifestSpec` at ``path`` to latest version including documentation."""
        # read
        content = path.read_text()
        try:
            olddoc = tomlkit.parse(content)
            olddata = dict(olddoc)
            olddata.pop("groups", None)
            obj = cls(**olddata)
        except Exception as exc:
            raise ManifestError(resolve_relative(path), str(exc)) from None

        # merge
        newdoc = cls._create()
        for key, value in olddata.items():
            newdoc[key] = value
        for key, value in as_dict(obj).items():
            newdoc[key] = value
        newdoc["version"] = "1.0"

        # write
        path.write_text(tomlkit.dumps(newdoc))

    @staticmethod
    def _create() -> tomlkit.TOMLDocument:
        doc = tomlkit.document()

        # Version
        doc.add("version", ManifestSpec().version)  # type: ignore
        # Intro
        add_info(
            doc,
            """
Git Workspace's Manifest. Please see the documentation at:

https://git-ws.readthedocs.io/en/latest/manual/manifest.html
""",
        )
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Group Filtering
        example = ManifestSpec(group_filters=GroupFilters(("-doc", "-feature@path")))
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add("group-filters", tomlkit.array())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Remotes
        example = ManifestSpec(remotes=[Remote(name="myremote", url_base="https://github.com/myuser")])
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add("remotes", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Defaults
        doc.add("defaults", as_dict(Defaults()))
        example = ManifestSpec(
            defaults=Defaults(
                remote="myserver", revision="main", groups=("test",), with_groups=("doc",), submodules=True
            )
        )
        add_comment(doc, "\n".join(example.dump(doc=tomlkit.document(), minimal=True).split("\n")[1:-1]))
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Dependencies
        add_info(doc, "A full flavored dependency using a 'remote':")
        example = ManifestSpec(
            dependencies=[
                ProjectSpec(
                    name="myname",
                    remote="remote",
                    sub_url="my.git",
                    revision="main",
                    path="mydir",
                    manifest_path="git-ws.toml",
                    groups=("group",),
                    linkfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="link0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="link1-in-workspace.txt"),
                    ],
                    copyfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="file0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="file1-in-workspace.txt"),
                    ],
                )
            ]
        )
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add(tomlkit.nl())

        add_info(doc, "A full flavored dependency using a 'url':")
        example = ManifestSpec(
            dependencies=[
                ProjectSpec(
                    name="myname",
                    url="https://github.com/myuser/my.git",
                    revision="main",
                    path="mydir",
                    manifest_path="git-ws.toml",
                    groups=("group",),
                    linkfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="link0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="link1-in-workspace.txt"),
                    ],
                    copyfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="file0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="file1-in-workspace.txt"),
                    ],
                )
            ]
        )
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add(tomlkit.nl())

        add_info(doc, "A minimal dependency:")
        example = ManifestSpec(dependencies=[ProjectSpec(name="my", submodules=None)])
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])

        doc.add("dependencies", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # linkfíles
        example = ManifestSpec(linkfiles=[FileRef(src="file-in-main-clone.txt", dest="link-in-workspace.txt")])
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add("linkfiles", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # copyfíles
        example = ManifestSpec(copyfiles=[FileRef(src="file-in-main-clone.txt", dest="file-in-workspace.txt")])
        add_comment(doc, example.dump(doc=tomlkit.document(), minimal=True)[:-1])
        doc.add("copyfiles", tomlkit.aot())

        # Done
        return doc


class AppConfigData(BaseSettings, extra=Extra.allow):
    """
    Configuration data of the application.

    This class holds the concrete configuration values of the application.
    The following values are defined:
    """

    manifest_path: Optional[str] = Field(
        description="The path (relative to the project's root folder) to the manifest file."
    )
    """
    The path of the manifest file within a repository.

    If this is not defined, the default is ``git-ws.toml``.

    This option can be overridden by specifying the ``GIT_WS_MANIFEST_PATH`` environment variable.
    """

    color_ui: Optional[bool] = Field(description="If set to true, the output the tool generates will be colored.")
    """
    Defines if outputs by the tool shall be colored.

    If this is not defined, output will be colored by default.

    This option can be overridden by specifying the ``GIT_WS_COLOR_UI`` environment variable.
    """

    group_filters: Optional[GroupFilters] = Field(description="The groups to operate on.")
    """
    The groups to operate on.

    This is a filter for groups to operate on during workspace actions.

    This option can be overridden by specifying the ``GIT_WS_GROUP_FILTERS`` environment variable.
    """

    clone_cache: Optional[Path] = Field(description="Local Cache for Git Clones.")
    """
    Clone Cache.

    Initial cloning all dependencies takes a while. This sums up if done often (i.e. in CI/CD).
    This local filesystem cache directory will be used, to re-use already cloned data.

    This option can be overridden by specifying the ``GIT_WS_CLONE_CACHE`` environment variable.
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
