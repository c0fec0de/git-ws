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
Central :any:`GitWS` Datamodel.

* :any:`AppConfigData`: :any:`GitWS` Configuration.
* :any:`Defaults`: Default Values.
* :any:`Group`: Dependency Group.
* :any:`Manifest`: Manifest as needed by :any:`GitWS`.
* :any:`ManifestSpec`: Specification of the actual project.
* :any:`Project`: A Single Dependency as needed by :any:`GitWS`.
* :any:`ProjectSpec`: Dependency Specification from Manifest File.
* :any:`Remote`: Remote Alias.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import tomlkit
from pydantic import BaseSettings, Extra, Field, root_validator

from ._basemodel import BaseModel
from ._url import urljoin, urlsub
from ._util import add_comment, add_info, as_dict, get_repr, resolve_relative
from .const import MANIFEST_PATH_DEFAULT
from .exceptions import ManifestError, ManifestNotFoundError


class Remote(BaseModel, allow_population_by_field_name=True):
    """
    Remote Alias.

    Args:
        name: Remote Name

    Keyword Args:
        url_base: Base URL. Optional.
    """

    name: str
    """The Name of the Remote. Must be unique within Manifest."""

    url_base: str = Field(None, alias="url-base")
    """URL to a directory of repositories."""


class Defaults(BaseModel):
    """
    Default Values.

    These default values are used, if the project does not specify them.

    Keyword Args:
        remote: Remote Name
        revision: Revision
    """

    remote: Optional[str] = None
    """Remote name if not specified by the dependency. The remote must have been defined previously."""

    revision: Optional[str] = None
    """The revision if not specified by the dependency. Tag or Branch. SHA does not make sense here."""


class Group(BaseModel):
    """
    Dependency Group.

    Dependency groups structure dependencies.
    Groups are optional by default.

    Args:
        name: Name

    Keyword Args:
        optional: Group is optional. Default is `True`.
    """

    name: str
    """Group Name."""

    optional: bool = True
    """Group is optional and not required. Default is `True`."""

    @property
    def info(self):
        """
        `repr`-like information string.

        >>> Group(name='name').info
        'name'
        >>> Group(name='name', optional=False).info
        '+name'
        >>> Group(name='name', optional=True).info
        'name'
        """
        if not self.optional:
            return f"+{self.name}"
        return self.name


class Project(BaseModel):

    """
    Project.

    A project describes a dependency.

    Args:
        name: Name.
        path: Project Filesystem Path. Relative to Workspace Root Directory.

    Keyword Args:
        url: URL
        revision: Revision
        manifest_path: Path to manifest. Relative to ProjectSpec Filesystem Path. `git-ws.toml` by default.
        groups: Dependency Groups.
        is_main: Project is Main Project.

    The :any:`ProjectSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Project` is the resolved version of :any:`ProjectSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    :any:`Project.from_spec()` resolves a :any:`ProjectSpec` into a :any:`Project`.
    :any:`ProjectSpec.from_project()` does the reverse.
    """

    name: str
    """Dependency Name."""

    path: str
    """Dependency Path. `name` will be used as default."""

    url: Optional[str] = None
    """URL. Assembled from `remote`s `url_base`, `sub_url` and/or `name`."""

    revision: Optional[str] = None
    """Revision to be checked out."""

    manifest_path: str = str(MANIFEST_PATH_DEFAULT)
    """Path to the manifest file. Relative to `path`."""

    groups: Tuple[Group, ...] = tuple()
    """Groups."""

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
        >>> Project(name='name', path='name', groups=(Group(name='test'), Group(name='doc', optional=False))).info
        "name (groups='test,+doc')"
        """
        options = get_repr(
            kwargs=(
                ("revision", self.revision, None),
                ("path", str(self.path), self.name),
                ("groups", ",".join(group.info for group in self.groups), ""),
            )
        )
        if self.is_main:
            options = f"MAIN {options}" if options else "MAIN"
        if options:
            return f"{self.name} ({options})"
        return self.name

    @staticmethod
    def from_spec(manifest_spec: "ManifestSpec", spec: "ProjectSpec", refurl: Optional[str] = None) -> "Project":
        """
        Create :any:`Project` from `manifest_spec` and `spec`.

        Args:
            manifest_spec:
            defaults: Default settings if not given by `spec`.
            remotes: Remotes
            spec: Base project to be resolved.

        :any:`Project.from_spec()` resolves a :any:`ProjectSpec` into a :any:`Project`.
        :any:`ProjectSpec.from_project()` does the reverse.
        """
        defaults = manifest_spec.defaults
        remotes = manifest_spec.remotes
        groups = manifest_spec.groups
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
        url = urljoin(refurl, url)
        groupdict = {group.name: group for group in groups} if spec.groups else {}
        return Project(
            name=spec.name,
            path=spec.path or spec.name,
            url=url,
            revision=spec.revision or defaults.revision,
            manifest_path=spec.manifest_path,
            groups=[groupdict.get(name, Group(name=name)) for name in spec.groups],
        )


class ProjectSpec(BaseModel, allow_population_by_field_name=True):
    """
    Project Dependency Specification

    A project specifies the reference to a repository.

    Args:
        name: Name.

    Keyword Args:
        remote: Remote Alias
        sub_url: URL relative to :any:`Remote.url_base`.
        url: URL
        revision: Revision
        path: Project Filesystem Path. Relative to Workspace Root Directory.
        manifest_path: Path to manifest. Relative to ProjectSpec Filesystem Path. `git-ws.toml` by default.
        groups: Dependency Groups.

    Some parameters are restricted:

    * `remote` and `url` are mutually exclusive.
    * `url` and `sub-url` are likewise mutually exclusive
    * `sub-url` requires a `remote`.

    The :any:`ProjectSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Project` is the resolved version of :any:`ProjectSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    :any:`Project.from_spec()` resolves a :any:`ProjectSpec` into a :any:`Project`.
    :any:`ProjectSpec.from_project()` does the reverse.
    """

    name: str
    """Dependency Name."""

    remote: Optional[str] = None
    """Remote Alias Name. The `remote` must have been defined previously."""

    sub_url: Optional[str] = Field(None, alias="sub-url")
    """Relative URL to `remote`s `url_base` OR the URL of the manifest file."""

    url: Optional[str] = None
    """Absolute URL."""

    revision: Optional[str] = None
    """Revision to be checked out."""

    path: Optional[str] = None
    """Path within workspace. `name` will be used as default."""

    manifest_path: str = str(MANIFEST_PATH_DEFAULT)
    """Path to the manifest file. Relative to `path`."""

    groups: Tuple[str, ...] = tuple()
    """Group Names."""

    @root_validator(allow_reuse=True)
    def _remote_or_url(cls, values):
        # pylint: disable=no-self-argument,no-self-use
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

    @staticmethod
    def from_project(project: Project) -> "ProjectSpec":
        """
        Create :any:`ProjectSpec` from `project`.

        Args:
            project: The source :any:`Project`.

        ..note::
            :any:`Project.from_spec()` resolves some attributes irreversible.
            So :any:`Project.from_spec(ProjectSpec.from_project())` will not
            return the original project.
        """
        return ProjectSpec(
            name=project.name,
            path=project.path,
            url=project.url,
            revision=project.revision,
            manifest_path=project.manifest_path,
            groups=[group.name for group in project.groups],
        )


class Manifest(BaseModel, extra=Extra.allow):

    """
    Manifest.

    A manifest describes the actual project and its dependencies.

    Keyword Args:
        groups: Groups.
        dependencies: Dependency Projects.
        path: Filesystem Path. Relative to Workspace Root Directory.


    The :any:`ManifestSpec` represents the User Interface. The options which can be specified in the manifest file.
    The :any:`Manifest` is the resolved version of :any:`ManifestSpec` with all calculated information needed by
    :any:`GitWS` to operate.

    :any:`Manifest.from_spec()` resolves a :any:`ManifestSpec` into a :any:`Manifest`.
    """

    groups: Tuple[Group, ...] = tuple()
    """Groups."""

    dependencies: Tuple[Project, ...] = tuple()
    """Dependencies."""

    path: Optional[str] = None
    """Path to the manifest file, relative to project path."""

    @staticmethod
    def from_spec(spec: "ManifestSpec", path: Optional[str] = None, refurl: Optional[str] = None) -> "Manifest":
        """
        Create :any:`Manifest` from :any:`ManifestSpec`.

        Args:
            spec: The source :any:`ManifestSpec`.

        Keyword Args:
            path: File path of the `spec`.
            refurl: URL of the repository containing `spec`.

        If `refurl` is specified, any relative URL in the :any:`ManifestSpec` and referred :any:`ProjectSpec` s
        is resolved to an absolute URL.
        """
        dependencies = [Project.from_spec(spec, project_spec, refurl=refurl) for project_spec in spec.dependencies]
        return Manifest(
            groups=spec.groups,
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
        groups: Groups.
        defaults: Default settings.
        dependencies: Dependency Projects.
    """

    version: str = Field(default="1.0")
    """
    Manifest Version Identifier.

    Actual Version: `1.0`.
    """

    remotes: Tuple[Remote, ...] = tuple()
    """Remotes."""

    groups: Tuple[Group, ...] = tuple()
    """Groups."""

    defaults: Defaults = Defaults()
    """Default Values."""

    dependencies: Tuple[ProjectSpec, ...] = tuple()
    """Dependencies."""

    @root_validator(allow_reuse=True)
    def _remotes_unique(cls, values):
        # pylint: disable=no-self-argument,no-self-use
        names = set()
        for remote in values.get("remotes", None) or []:
            name = remote.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Remote name {name!r} is used more than once")
        return values

    @root_validator(allow_reuse=True)
    def _groups_unique(cls, values):
        # pylint: disable=no-self-argument,no-self-use
        names = set()
        for group in values.get("groups", None) or []:
            name = group.name
            if name not in names:
                names.add(name)
            else:
                raise ValueError(f"Group name {name!r} is used more than once")
        return values

    @classmethod
    def load(cls, path: Path) -> "ManifestSpec":
        """
        Load :any:`ManifestSpec` from `path`.

        The file referenced by `path` should be a TOML file according to the
        manifest scheme.

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

    def dump(self, doc: Optional[tomlkit.TOMLDocument] = None, path: Optional[Path] = None) -> str:
        """
        Return :any:`ManifestSpec` as string.

        The output will include an inline documentation of all available options.
        If `doc` or `path` are specified, any additional attributes and comments added by the user before
        are **kept**.

        Args:
            doc: Existing document to be updated.
            path: Path to possibly existing document.
        """
        assert not doc or not path, "'doc' and 'path' are mutually exclusive."
        if doc is None:
            if path and path.exists():
                doc = tomlkit.parse(path.read_text())
            else:
                doc = self._create()
        for key, value in as_dict(self).items():
            doc[key] = value
        return tomlkit.dumps(doc)

    def save(self, path: Path, update=True):
        """
        Save :any:`ManifestSpec` at `path`.

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
        """Upgrade :any:`ManifestSpec` at `path` to latest revision including documentation."""
        # read
        content = path.read_text()
        try:
            olddoc = tomlkit.parse(content)
            data = dict(olddoc)
            obj = cls(**data)
        except Exception as exc:
            raise ManifestError(resolve_relative(path), str(exc)) from None

        # merge
        newdoc = cls._create()
        for key, value in olddoc.items():
            newdoc[key] = value
        for key, value in as_dict(obj).items():
            newdoc[key] = value

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
Welcome to Git Workspace's Manifest. It actually contains 4 parts:

* Remotes
* Groups
* Defaults
* Dependencies
""",
        )

        # Remotes
        add_info(
            doc,
            """\
=========
 Remotes
=========

Remotes just refer to a directory with repositories.

We support relative paths for dependencies. So, if your dependencies are next
to your repository, you might NOT need any remote.
In other terms: You only need remotes if your dependencies are located on
OTHER servers than your server with this manifest.

Remotes have two attributes:
* name: Required. String.
        Name of the remote. Any valid string. Must be unique within your
        manifest.
* url-base: Required. String.
            URL Prefix. The project 'name' or 'sub-url' will be appended
            later-on.
""",
        )
        example = ManifestSpec(remotes=[Remote(name="myremote", url_base="https://github.com/myuser")])
        add_comment(doc, example.dump(doc=tomlkit.document())[:-1])
        doc.add("remotes", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Groups
        add_info(
            doc,
            """\
=========
 Groups
=========

Groups structure dependencies.

Groups are optional by default.
If a dependency belongs to a group, it becomes optional likewise.
Groups can be later on selected/deselected by '+group' or '-group'.
An optional group can be selected by '+group',
a non-optional group can be deselected by '-group'.
Deselection has higher priority than selection.

Dependencies can refer to non-existing groups. You do NOT need to specify
all used groups.

Groups have two attributes:
* name: Required. String.
        Name of the group. Any valid string. Must be unique within your
        manifest.
* optional: Optional. Bool. Default is True.
            Specifies if the group is optional. Meaning it must be selected
            explicitly. Otherwise the dependency is not added by default.

The following lines set a group as non-optional.""",
        )
        example = ManifestSpec(groups=[Group(name="test", optional=False)])
        add_comment(doc, example.dump(doc=tomlkit.document())[:-1])
        doc.add("groups", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Defaults
        add_info(
            doc,
            """\
==========
 Defaults
==========

The 'defaults' section specifies default values for dependencies.

* remote: Optional. String.
          Remote used as default.
          The 'remote' MUST be defined in the 'remotes' section above!
* revision: Optional. String.
            Revision used as default. Tag or Branch.

NOTE: It is recommended to specify a default revision (i.e. 'main').
      If a dependency misses 'revision', GitWS will not take care about
      revision handling. This may lead to strange side-effects. You
      have been warned.""",
        )

        doc.add("defaults", as_dict(Defaults()))
        example = ManifestSpec(defaults=Defaults(remote="myserver", revision="main"))
        add_comment(doc, "\n".join(example.dump(doc=tomlkit.document()).split("\n")[1:-1]))
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Dependencies
        add_info(
            doc,
            """\
==============
 Dependencies
==============

The 'dependencies' section specifies all your git clones you need for your
project to operate.

A dependency has the following attributes:
* name: Required. String.
        Just name your dependency. It is recommended to choose a
        unique name, but not a must.
* remote: Optional. String. Restricted (see RESTRICTIONS below).
          Remote Alias.
          The 'remote' MUST be defined in the 'remotes' section above!
          The 'remote' can also be specified in the 'defaults' section.
* sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).
           Relative URL to 'url-base' of your specified 'remote'
           OR
           Relative URL to the URL of the repository containing this
           manifest.
* url: Optional. String. Restricted (see RESTRICTIONS below).
       Absolute URL to the dependent repository.
* revision: Optional. String.
            Revision to be checked out.
            If this attribute is left blank, GitWS does NOT manage the
            dependency revision (see NOTE2 below)!
            The 'revision' can also be specified in the 'defaults' section.
* path: Optional. String. Default is '{name}'.
        Project Filesystem Path. Relative to Workspace Root Directory.
        The dependency 'name' is used as default for 'path'.
        The 'path' MUST be unique within your manifest.
* manifest_path: Optional. String. Default: 'git-ws.toml'.
                  Path to manifest.
                  Relative to 'path'.
                  Avoid changing it! It is just additional effort.
* groups: Optional. List of Strings.
          Dependency Groups.
          Dependencies can be categorized into groups.
          Groups are optional by default. See 'groups' section above.

NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency
       is next to your repository containing this manifest, the dependency
       is automatically found.
       The '.git' suffix is appended if the repository containing this
       manifest uses a '.git' suffix.

NOTE2: It is recommended to specify a revision (i.e. 'main') either
       explicitly or via the 'default' section.
       Without a 'revision' GitWS will not take care about revision
       handling. This may lead to strange side-effects.
       You have been warned.

RESTRICTIONS:

* `remote` and `url` are mutually exclusive.
* `url` and `sub-url` are likewise mutually exclusive
* `sub-url` requires a `remote`.


A full flavored dependency using a 'remote':""",
        )

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
                )
            ]
        )
        add_comment(doc, example.dump(doc=tomlkit.document())[:-1])
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
                )
            ]
        )
        add_comment(doc, example.dump(doc=tomlkit.document())[:-1])
        doc.add(tomlkit.nl())

        add_info(doc, "A minimal dependency:")
        example = ManifestSpec(dependencies=[ProjectSpec(name="my")])
        add_comment(doc, example.dump(doc=tomlkit.document())[:-1])

        doc.add("dependencies", tomlkit.aot())

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

    If this is not defined, the default is :any:`MANIFEST_PATH_DEFAULT`.

    This option can be overridden by specifying the `GIT_WS_MANIFEST_PATH` environment variable.
    """

    color_ui: Optional[bool] = Field(description="If set to true, the output the tool generates will be colored.")
    """
    Defines if outputs by the tool shall be colored.

    If this is not defined, output will be colored by default.

    This option can be overridden by specifying the `GIT_WS_COLOR_UI` environment variable.
    """

    groups: Optional[str] = Field(description="The groups to operate on.")
    """
    The groups to operate on.

    This is a filter for groups to operate on during workspace actions.

    This option can be overridden by specifying the `GIT_WS_GROUPS` environment variable.
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
