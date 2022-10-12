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

"""Manifest Testing."""
from pytest import raises

from gitws.datamodel import Defaults, Group, Manifest, ManifestSpec, Project, ProjectSpec, Remote

from .common import MANIFEST_DEFAULT


def test_remote():
    """Test Remotes."""
    remote = Remote(name="origin")
    assert remote.name == "origin"
    assert remote.url_base is None

    remote = Remote(name="origin2", url_base="base")
    assert remote.name == "origin2"
    assert remote.url_base == "base"

    # Immutable
    with raises(TypeError):
        remote.name = "other"


def test_defaults():
    """Test Defaults."""
    defaults = Defaults()
    assert defaults.remote is None
    assert defaults.revision is None

    defaults = Defaults(remote="remote")
    assert defaults.remote == "remote"
    assert defaults.revision is None

    defaults = Defaults(revision="Revision")
    assert defaults.remote is None
    assert defaults.revision == "Revision"

    # Immutable
    with raises(TypeError):
        defaults.remote = "other"


def test_project_group():
    """Group."""
    group = Group(name="name")
    assert group.name == "name"
    assert group.optional

    group = Group(name="name", optional=False)
    assert group.name == "name"
    assert not group.optional

    # Immutable
    with raises(TypeError):
        group.name = "other"


def test_project_spec():
    """Test ProjectSpec."""
    project_spec = ProjectSpec(name="name")
    assert project_spec.name == "name"
    assert project_spec.remote is None
    assert project_spec.sub_url is None
    assert project_spec.url is None
    assert project_spec.revision is None

    with raises(ValueError):
        ProjectSpec(name="name", remote="remote", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url")

    # Immutable
    with raises(TypeError):
        project_spec.name = "other"


def test_manifest_spec(tmp_path):
    """Test ManifestSpec."""
    manifest_spec = ManifestSpec()
    assert manifest_spec.defaults == Defaults()
    assert not manifest_spec.remotes
    assert not manifest_spec.dependencies

    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
    assert filepath.read_text() == MANIFEST_DEFAULT


def test_manifest_spec_save(tmp_path):
    """Manifest Saving."""
    manifest_spec = ManifestSpec(
        remotes=[Remote(name="name")],
        groups=(Group(name="group", optional=False), Group(name="group2")),
        dependencies=(ProjectSpec(name="dep"),),
    )
    text = """\
version = "1.0"
##
## Welcome to Git Workspace's Manifest. It actually contains 4 parts:
##
## * Remotes
## * Groups
## * Defaults
## * Dependencies
##
## =========
##  Remotes
## =========
##
## Remotes just refer to a directory with repositories.
##
## We support relative paths for dependencies. So, if your dependencies are next
## to your repository, you might NOT need any remote.
## In other terms: You only need remotes if your dependencies are located on
## OTHER servers than your server with this manifest.
##
## Remotes have two attributes:
## * name: Required. String.
##         Name of the remote. Any valid string. Must be unique within your
##         manifest.
## * url-base: Required. String.
##             URL Prefix. The project 'name' or 'sub-url' will be appended
##             later-on.
##
# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
[[remotes]]
name = "name"


## =========
##  Groups
## =========
##
## Groups structure dependencies.
##
## Groups are optional by default.
## If a dependency belongs to a group, it becomes optional likewise.
## Groups can be later on selected/deselected by '+group' or '-group'.
## An optional group can be selected by '+group',
## a non-optional group can be deselected by '-group'.
## Deselection has higher priority than selection.
##
## Dependencies can refer to non-existing groups. You do NOT need to specify
## all used groups.
##
## Groups have two attributes:
## * name: Required. String.
##         Name of the group. Any valid string. Must be unique within your
##         manifest.
## * optional: Optional. Bool. Default is True.
##             Specifies if the group is optional. Meaning it must be selected
##             explicitly. Otherwise the dependency is not added by default.
##
## The following lines set a group as non-optional.
# [[groups]]
# name = "test"
# optional = false
[[groups]]
name = "group"
optional = false

[[groups]]
name = "group2"


## ==========
##  Defaults
## ==========
##
## The 'defaults' section specifies default values for dependencies.
##
## * remote: Optional. String.
##           Remote used as default.
##           The 'remote' MUST be defined in the 'remotes' section above!
## * revision: Optional. String.
##             Revision used as default. Tag or Branch.
##
## NOTE: It is recommended to specify a default revision (i.e. 'main').
##       If a dependency misses 'revision', GitWS will not take care about
##       revision handling. This may lead to strange side-effects. You
##       have been warned.

[defaults]
# remote = "myserver"
# revision = "main"


## ==============
##  Dependencies
## ==============
##
## The 'dependencies' section specifies all your git clones you need for your
## project to operate.
##
## A dependency has the following attributes:
## * name: Required. String.
##         Just name your dependency. It is recommended to choose a
##         unique name, but not a must.
## * remote: Optional. String. Restricted (see RESTRICTIONS below).
##           Remote Alias.
##           The 'remote' MUST be defined in the 'remotes' section above!
##           The 'remote' can also be specified in the 'defaults' section.
## * sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).
##            Relative URL to 'url-base' of your specified 'remote'
##            OR
##            Relative URL to the URL of the repository containing this
##            manifest.
## * url: Optional. String. Restricted (see RESTRICTIONS below).
##        Absolute URL to the dependent repository.
## * revision: Optional. String.
##             Revision to be checked out.
##             If this attribute is left blank, GitWS does NOT manage the
##             dependency revision (see NOTE2 below)!
##             The 'revision' can also be specified in the 'defaults' section.
## * path: Optional. String. Default is '{name}'.
##         Project Filesystem Path. Relative to Workspace Root Directory.
##         The dependency 'name' is used as default for 'path'.
##         The 'path' MUST be unique within your manifest.
## * manifest_path: Optional. String. Default: 'git-ws.toml'.
##                   Path to manifest.
##                   Relative to 'path'.
##                   Avoid changing it! It is just additional effort.
## * groups: Optional. List of Strings.
##           Dependency Groups.
##           Dependencies can be categorized into groups.
##           Groups are optional by default. See 'groups' section above.
##
## NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency
##        is next to your repository containing this manifest, the dependency
##        is automatically found.
##        The '.git' suffix is appended if the repository containing this
##        manifest uses a '.git' suffix.
##
## NOTE2: It is recommended to specify a revision (i.e. 'main') either
##        explicitly or via the 'default' section.
##        Without a 'revision' GitWS will not take care about revision
##        handling. This may lead to strange side-effects.
##        You have been warned.
##
## RESTRICTIONS:
##
## * `remote` and `url` are mutually exclusive.
## * `url` and `sub-url` are likewise mutually exclusive
## * `sub-url` requires a `remote`.
##
##
## A full flavored dependency using a 'remote':
# [[dependencies]]
# name = "myname"
# remote = "remote"
# sub-url = "my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A full flavored dependency using a 'url':
# [[dependencies]]
# name = "myname"
# url = "https://github.com/myuser/my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A minimal dependency:
# [[dependencies]]
# name = "my"
[[dependencies]]
name = "dep"
"""
    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
    assert filepath.read_text() == text

    # empty one
    filepath = tmp_path / "empty.toml"
    filepath.touch()
    manifest_spec.save(filepath)
    assert (
        filepath.read_text()
        == """\
[[remotes]]
name = "name"

[[groups]]
name = "group"
optional = false

[[groups]]
name = "group2"

[[dependencies]]
name = "dep"
"""
    )

    # empty one
    filepath = tmp_path / "empty.toml"
    filepath.touch()
    manifest_spec.save(filepath, update=False)
    assert filepath.read_text() == text

    # Immutable
    with raises(TypeError):
        manifest_spec.defaults = Defaults()


def test_manifest_spec_from_data(tmp_path):
    """Determine ManifestSpec from Data."""
    data = {
        "defaults": {
            "remote": "remote1",
            "revision": "v1.3",
        },
        "remotes": [
            {"name": "remote2", "url-base": "https://git.example.com/base2"},
            {"name": "remote1", "url-base": "https://git.example.com/base1"},
        ],
        "groups": [
            {"name": "foo", "optional": False},
            {"name": "bar"},
        ],
        "dependencies": [
            {"name": "dep1", "remote": "remote1", "groups": ["test", "foo"]},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    assert manifest_spec.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest_spec.remotes == (
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    )
    assert manifest_spec.groups == (Group(name="foo", optional=False), Group(name="bar"))
    assert manifest_spec.dependencies == (
        ProjectSpec(name="dep1", remote="remote1", groups=("test", "foo")),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    )

    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
    assert (
        filepath.read_text()
        == """version = "1.0"
##
## Welcome to Git Workspace's Manifest. It actually contains 4 parts:
##
## * Remotes
## * Groups
## * Defaults
## * Dependencies
##
## =========
##  Remotes
## =========
##
## Remotes just refer to a directory with repositories.
##
## We support relative paths for dependencies. So, if your dependencies are next
## to your repository, you might NOT need any remote.
## In other terms: You only need remotes if your dependencies are located on
## OTHER servers than your server with this manifest.
##
## Remotes have two attributes:
## * name: Required. String.
##         Name of the remote. Any valid string. Must be unique within your
##         manifest.
## * url-base: Required. String.
##             URL Prefix. The project 'name' or 'sub-url' will be appended
##             later-on.
##
# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
[[remotes]]
name = "remote2"
url-base = "https://git.example.com/base2"

[[remotes]]
name = "remote1"
url-base = "https://git.example.com/base1"


## =========
##  Groups
## =========
##
## Groups structure dependencies.
##
## Groups are optional by default.
## If a dependency belongs to a group, it becomes optional likewise.
## Groups can be later on selected/deselected by '+group' or '-group'.
## An optional group can be selected by '+group',
## a non-optional group can be deselected by '-group'.
## Deselection has higher priority than selection.
##
## Dependencies can refer to non-existing groups. You do NOT need to specify
## all used groups.
##
## Groups have two attributes:
## * name: Required. String.
##         Name of the group. Any valid string. Must be unique within your
##         manifest.
## * optional: Optional. Bool. Default is True.
##             Specifies if the group is optional. Meaning it must be selected
##             explicitly. Otherwise the dependency is not added by default.
##
## The following lines set a group as non-optional.
# [[groups]]
# name = "test"
# optional = false
[[groups]]
name = "foo"
optional = false

[[groups]]
name = "bar"


## ==========
##  Defaults
## ==========
##
## The 'defaults' section specifies default values for dependencies.
##
## * remote: Optional. String.
##           Remote used as default.
##           The 'remote' MUST be defined in the 'remotes' section above!
## * revision: Optional. String.
##             Revision used as default. Tag or Branch.
##
## NOTE: It is recommended to specify a default revision (i.e. 'main').
##       If a dependency misses 'revision', GitWS will not take care about
##       revision handling. This may lead to strange side-effects. You
##       have been warned.

[defaults]
remote = "remote1"
revision = "v1.3"

# remote = "myserver"
# revision = "main"


## ==============
##  Dependencies
## ==============
##
## The 'dependencies' section specifies all your git clones you need for your
## project to operate.
##
## A dependency has the following attributes:
## * name: Required. String.
##         Just name your dependency. It is recommended to choose a
##         unique name, but not a must.
## * remote: Optional. String. Restricted (see RESTRICTIONS below).
##           Remote Alias.
##           The 'remote' MUST be defined in the 'remotes' section above!
##           The 'remote' can also be specified in the 'defaults' section.
## * sub-url: Optional. String. Default: '../{name}[.git]' (see NOTE1 below).
##            Relative URL to 'url-base' of your specified 'remote'
##            OR
##            Relative URL to the URL of the repository containing this
##            manifest.
## * url: Optional. String. Restricted (see RESTRICTIONS below).
##        Absolute URL to the dependent repository.
## * revision: Optional. String.
##             Revision to be checked out.
##             If this attribute is left blank, GitWS does NOT manage the
##             dependency revision (see NOTE2 below)!
##             The 'revision' can also be specified in the 'defaults' section.
## * path: Optional. String. Default is '{name}'.
##         Project Filesystem Path. Relative to Workspace Root Directory.
##         The dependency 'name' is used as default for 'path'.
##         The 'path' MUST be unique within your manifest.
## * manifest_path: Optional. String. Default: 'git-ws.toml'.
##                   Path to manifest.
##                   Relative to 'path'.
##                   Avoid changing it! It is just additional effort.
## * groups: Optional. List of Strings.
##           Dependency Groups.
##           Dependencies can be categorized into groups.
##           Groups are optional by default. See 'groups' section above.
##
## NOTE1: 'sub-url' is '../{name}[.git]' by default. Meaning if the dependency
##        is next to your repository containing this manifest, the dependency
##        is automatically found.
##        The '.git' suffix is appended if the repository containing this
##        manifest uses a '.git' suffix.
##
## NOTE2: It is recommended to specify a revision (i.e. 'main') either
##        explicitly or via the 'default' section.
##        Without a 'revision' GitWS will not take care about revision
##        handling. This may lead to strange side-effects.
##        You have been warned.
##
## RESTRICTIONS:
##
## * `remote` and `url` are mutually exclusive.
## * `url` and `sub-url` are likewise mutually exclusive
## * `sub-url` requires a `remote`.
##
##
## A full flavored dependency using a 'remote':
# [[dependencies]]
# name = "myname"
# remote = "remote"
# sub-url = "my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A full flavored dependency using a 'url':
# [[dependencies]]
# name = "myname"
# url = "https://github.com/myuser/my.git"
# revision = "main"
# path = "mydir"
# groups = ["group"]

## A minimal dependency:
# [[dependencies]]
# name = "my"
[[dependencies]]
name = "dep1"
remote = "remote1"
groups = ["test", "foo"]

[[dependencies]]
name = "dep2"
url = "https://git.example.com/base3/dep2.git"
path = "dep2dir"

[[dependencies]]
name = "dep3"
remote = "remote1"
sub-url = "sub.git"
revision = "main"
"""
    )
    assert ManifestSpec.load(filepath) == manifest_spec

    rdependencies = [Project.from_spec(manifest_spec, project) for project in manifest_spec.dependencies]
    assert rdependencies == [
        Project(
            name="dep1",
            url="https://git.example.com/base1/dep1",
            revision="v1.3",
            path="dep1",
            groups=(Group(name="test"), Group(name="foo", optional=False)),
        ),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", revision="v1.3", path="dep2dir"),
        Project(name="dep3", url="https://git.example.com/base1/sub.git", revision="main", path="dep3"),
    ]


def test_manifest_spec_from_other_data():
    """Determine ManifestSpec from Other Data."""
    data = {
        "defaults": {
            "remote": "remote1",
        },
        "dependencies": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest = ManifestSpec(**data)
    assert manifest.defaults == Defaults(remote="remote1")
    assert not manifest.remotes
    assert manifest.dependencies == (
        ProjectSpec(name="dep1", remote="remote1"),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    )


def test_manifest_spec_not_remote():
    """Determine ManifestSpec from Other Data."""
    remotes = (Remote(name="remote2", url_base="foo"),)
    manifest_spec = ManifestSpec(remotes=remotes)
    project = Project.from_spec(manifest_spec, spec=ProjectSpec(name="foo"))
    assert project.name == "foo"
    assert project.url == "../foo"


def test_manifest_spec_missing_remote():
    """Determine ManifestSpec with missing Remote."""
    remotes = (Remote(name="remote2", url_base="foo"),)
    manifest_spec = ManifestSpec(remotes=remotes)
    with raises(ValueError) as exc:
        Project.from_spec(manifest_spec, spec=ProjectSpec(name="foo", remote="remote1"))
    assert str(exc.value) == "Unknown remote remote1 for project foo"


def test_manifest():
    """Test Manifest."""
    data = {
        "remotes": [
            {
                "name": "remote1",
                "url-base": "url1",
            },
            {
                "name": "remote2",
                "url-base": "url2",
            },
        ],
        "defaults": {
            "remote": "remote1",
        },
        "groups": [
            {"name": "doc", "optional": True},
            {"name": "bar"},
        ],
        "dependencies": [
            {"name": "dep1", "remote": "remote2", "groups": ["test", "doc"]},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main", "groups": ["test"]},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    manifest = Manifest.from_spec(manifest_spec)
    assert manifest.dependencies == (
        Project(
            name="dep1", path="dep1", url="url2/dep1", groups=(Group(name="test"), Group(name="doc", optional=True))
        ),
        Project(name="dep2", path="dep2dir", url="https://git.example.com/base3/dep2.git"),
        Project(name="dep3", path="dep3", url="url1/sub.git", revision="main", groups=(Group(name="test"),)),
    )
    assert manifest.path is None


def test_default_url():
    """Top should be default URL."""
    data = {
        "dependencies": [
            {"name": "dep1"},
            {"name": "dep2"},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    assert not manifest_spec.remotes
    assert not manifest_spec.groups
    assert manifest_spec.dependencies == (
        ProjectSpec(name="dep1"),
        ProjectSpec(name="dep2"),
    )

    manifest = Manifest.from_spec(manifest_spec)
    assert not manifest.groups
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="../dep1"),
        Project(name="dep2", path="dep2", url="../dep2"),
    )

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main")
    assert not manifest.groups
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2"),
    )

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.git")
    assert not manifest.groups
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1.git"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2.git"),
    )

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.suffix")
    assert not manifest.groups
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1.suffix"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2.suffix"),
    )


def test_remotes_unique():
    """Remote names must be unique."""
    with raises(ValueError):
        ManifestSpec(remotes=(Remote(name="foo", url_base="url"), Remote(name="foo", url_base="url")))


def test_groups_unique():
    """Group names must be unique."""
    with raises(ValueError):
        ManifestSpec(groups=(Group(name="foo"), Group(name="foo")))
