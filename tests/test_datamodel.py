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

"""Manifest Testing."""
from pytest import raises

from gitws import (
    Defaults,
    FileRef,
    Groups,
    GroupSelect,
    GroupSelects,
    Manifest,
    ManifestSpec,
    Project,
    ProjectSpec,
    Remote,
)

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
    assert defaults.groups == tuple()
    assert defaults.with_groups == tuple()

    defaults = Defaults(remote="remote")
    assert defaults.remote == "remote"
    assert defaults.revision is None
    assert defaults.groups == tuple()
    assert defaults.with_groups == tuple()

    defaults = Defaults(revision="Revision")
    assert defaults.remote is None
    assert defaults.revision == "Revision"
    assert defaults.groups == tuple()
    assert defaults.with_groups == tuple()

    defaults = Defaults(groups=("test", "doc"))
    assert defaults.remote is None
    assert defaults.revision is None
    assert defaults.groups == ("test", "doc")
    assert defaults.with_groups == tuple()

    defaults = Defaults(with_groups=("test", "doc"))
    assert defaults.remote is None
    assert defaults.revision is None
    assert defaults.groups == tuple()
    assert defaults.with_groups == ("test", "doc")

    # Immutable
    with raises(TypeError):
        defaults.remote = "other"

    with raises(ValueError) as exc:
        Defaults(groups=("-foo",))
    assert str(exc.value).split("\n") == [
        "1 validation error for Defaults",
        "groups",
        "  Invalid group '-foo' (type=value_error)",
    ]

    with raises(ValueError) as exc:
        Defaults(with_groups=("-foo",))
    assert str(exc.value).split("\n") == [
        "1 validation error for Defaults",
        "with-groups",
        "  Invalid group '-foo' (type=value_error)",
    ]


def test_group_select():
    """Group Select."""
    group_select = GroupSelect(group="foo", select=True, path="path")
    assert group_select.group == "foo"
    assert group_select.select
    assert group_select.path == "path"
    assert str(group_select) == "+foo@path"

    # Immutable
    with raises(TypeError):
        group_select.group = "blub"


def test_group_selects():
    """Group Selects."""
    group_selects = GroupSelects.from_group_filters(("-test", "+doc", "+feature@path"))
    assert [str(group_select) for group_select in group_selects] == ["-test", "+doc", "+feature@path"]


def test_project():
    """Test ProjectSpec."""
    project = Project(name="name", path="path")
    assert project.name == "name"
    assert project.url is None
    assert project.revision is None
    assert project.manifest_path == "git-ws.toml"
    assert project.groups == Groups()
    assert project.with_groups == Groups()
    assert project.submodules is True
    assert project.linkfiles == tuple()
    assert project.copyfiles == tuple()
    assert project.info == "name (path='path')"

    # Immutable
    with raises(TypeError):
        project.name = "other"

    with raises(ValueError):
        Project(name="name", path="path", groups=("-foo",))

    with raises(ValueError):
        Project(name="name", path="path", with_groups=("-foo",))

    project = Project(
        name="name",
        path="path",
        url="url",
        is_main=True,
        groups=("a", "b"),
        with_groups=("c", "d"),
        submodules=True,
        linkfiles=[{"src": "src0", "dest": "dest0"}, {"src": "src1", "dest": "dest1"}],
        copyfiles=[{"src": "src2", "dest": "dest2"}, {"src": "src3", "dest": "dest3"}],
    )
    assert project.name == "name"
    assert project.url == "url"
    assert project.revision is None
    assert project.manifest_path == "git-ws.toml"
    assert project.groups == Groups(("a", "b"))
    assert project.with_groups == Groups(("c", "d"))
    assert project.linkfiles == (FileRef(src="src0", dest="dest0"), FileRef(src="src1", dest="dest1"))
    assert project.copyfiles == (FileRef(src="src2", dest="dest2"), FileRef(src="src3", dest="dest3"))
    assert project.info == "name (MAIN path='path', groups='a,b')"


def test_project_spec():
    """Test ProjectSpec."""
    project_spec = ProjectSpec(name="name")
    assert project_spec.name == "name"
    assert project_spec.remote is None
    assert project_spec.sub_url is None
    assert project_spec.url is None
    assert project_spec.revision is None
    assert project_spec.path is None
    assert project_spec.manifest_path == "git-ws.toml"
    assert project_spec.groups == Groups()
    assert project_spec.with_groups == Groups()
    assert project_spec.submodules is None
    assert project_spec.copyfiles == tuple()
    assert project_spec.linkfiles == tuple()

    with raises(ValueError):
        ProjectSpec(name="name", remote="remote", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url")

    # Immutable
    with raises(TypeError):
        project_spec.name = "other"

    with raises(ValueError) as exc:
        ProjectSpec(name="name", groups=("-foo",))
    assert str(exc.value).split("\n") == [
        "1 validation error for ProjectSpec",
        "groups",
        "  Invalid group '-foo' (type=value_error)",
    ]

    with raises(ValueError) as exc:
        ProjectSpec(name="name", with_groups=("-foo",))
    assert str(exc.value).split("\n") == [
        "1 validation error for ProjectSpec",
        "with-groups",
        "  Invalid group '-foo' (type=value_error)",
    ]


def test_manifest():
    """Test Manifest."""
    manifest = Manifest()
    assert not manifest.group_filters
    assert not manifest.dependencies

    # Immutable
    with raises(TypeError):
        manifest.defaults = Defaults()

    with raises(ValueError):
        Manifest(group_filters=("test",))


def test_manifest_spec():
    """Test ManifestSpec."""
    manifest_spec = ManifestSpec()
    assert manifest_spec.version == "1.0"
    assert not manifest_spec.remotes
    assert not manifest_spec.group_filters
    assert manifest_spec.defaults == Defaults()
    assert not manifest_spec.dependencies

    # Immutable
    with raises(TypeError):
        manifest_spec.defaults = Defaults()

    with raises(ValueError):
        ManifestSpec(group_filters=("test",))


def test_manifest_spec_save(tmp_path):
    """Manifest Saving."""
    filepath = tmp_path / "manifest.toml"
    ManifestSpec().save(filepath)
    assert filepath.read_text() == MANIFEST_DEFAULT

    manifest_spec = ManifestSpec(
        version="1.1",
        remotes=[Remote(name="remote")],
        group_filters=("+test",),
        defaults=Defaults(remote="remote"),
        dependencies=(
            ProjectSpec(
                name="dep",
                linkfiles=(
                    FileRef(src="src0", dest="subdir/dest0"),
                    FileRef(src="src1", dest="subdir/dest1"),
                ),
                copyfiles=(
                    FileRef(src="src2", dest="subdir/dest2"),
                    FileRef(src="src3", dest="subdir/dest3"),
                ),
            ),
        ),
    )
    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
    manifest = """\
version = "1.1"
##
## Git Workspace's Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/latest/manual/manifest.html
##


# group-filters = ["-doc", "-feature@path"]
group-filters = ["+test"]


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"


[defaults]
remote = "remote"


[[remotes]]
name = "remote"

[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"
"""
    assert filepath.read_text() == manifest

    filepath = tmp_path / "empty.toml"
    filepath.touch()
    manifest_spec.save(filepath)
    empty = """\
version = "1.1"
group-filters = ["+test"]

[[remotes]]
name = "remote"

[defaults]
remote = "remote"

[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"
"""
    assert filepath.read_text() == empty

    filepath = tmp_path / "update.toml"
    filepath.touch()
    manifest_spec.save(filepath, update=False)
    update = """\
version = "1.1"
##
## Git Workspace's Manifest. Please see the documentation at:
##
## https://git-ws.readthedocs.io/en/latest/manual/manifest.html
##


# group-filters = ["-doc", "-feature@path"]
group-filters = ["+test"]


# [[remotes]]
# name = "myremote"
# url-base = "https://github.com/myuser"
[[remotes]]
name = "remote"


[defaults]
remote = "remote"

# remote = "myserver"
# revision = "main"
# groups = ["test"]
# with-groups = ["doc"]


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

## A minimal dependency:
# [[dependencies]]
# name = "my"
[[dependencies]]
name = "dep"

[[dependencies.linkfiles]]
src = "src0"
dest = "subdir/dest0"

[[dependencies.linkfiles]]
src = "src1"
dest = "subdir/dest1"

[[dependencies.copyfiles]]
src = "src2"
dest = "subdir/dest2"

[[dependencies.copyfiles]]
src = "src3"
dest = "subdir/dest3"


# [[linkfiles]]
# src = "file-in-main-clone.txt"
# dest = "link-in-workspace.txt"


# [[copyfiles]]
# src = "file-in-main-clone.txt"
# dest = "file-in-workspace.txt"
"""
    assert filepath.read_text() == update


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
        "group-filters": ["+foo", "-bar"],
        "dependencies": [
            {
                "name": "dep1",
                "remote": "remote1",
                "groups": [
                    "test",
                    "foo",
                ],
                "linkfiles": [
                    {"src": "s0", "dest": "d0"},
                    {"src": "s1", "dest": "d1"},
                ],
            },
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main", "submodules": False},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    assert manifest_spec.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest_spec.remotes == (
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    )
    assert manifest_spec.group_filters == ("+foo", "-bar")
    assert manifest_spec.dependencies == (
        ProjectSpec(
            name="dep1",
            remote="remote1",
            groups=("test", "foo"),
            linkfiles=(
                {"src": "s0", "dest": "d0"},
                {"src": "s1", "dest": "d1"},
            ),
        ),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main", submodules=False),
    )

    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
    assert ManifestSpec.load(filepath) == manifest_spec


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
    manifest_spec = ManifestSpec(**data)
    assert manifest_spec.version == "1.0"
    assert not manifest_spec.remotes
    assert manifest_spec.defaults == Defaults(remote="remote1")
    assert manifest_spec.dependencies == (
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


def test_manifest_from_spec():
    """Test Manifest."""
    data = {
        "remotes": [
            {
                "name": "remote1",
                "url-base": "file:///repos/url1",
            },
            {
                "name": "remote2",
                "url-base": "file:///repos/url2",
            },
        ],
        "defaults": {
            "remote": "remote1",
        },
        "group-filters": ["-doc", "-bar"],
        "dependencies": [
            {
                "name": "dep1",
                "remote": "remote2",
                "groups": ["test", "doc"],
                "symlinks": [
                    {"src": "ss0", "dest": "dd0"},
                    {"src": "ss1", "dest": "dd1"},
                ],
                "linkfiles": [
                    {"src": "ss0", "dest": "dd0"},
                    {"src": "ss1", "dest": "dd1"},
                ],
                "copyfiles": [
                    {"src": "ss2", "dest": "dd2"},
                    {"src": "ss3", "dest": "dd3"},
                ],
            },
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main", "groups": ["test"]},
        ],
    }
    manifest_spec = ManifestSpec(**data)

    manifest = Manifest.from_spec(manifest_spec)
    assert manifest.group_filters == ("-doc", "-bar")
    assert manifest.dependencies == (
        Project(
            name="dep1",
            path="dep1",
            url="file:///repos/url2/dep1",
            groups=("test", "doc"),
            linkfiles=(
                {"src": "ss0", "dest": "dd0"},
                {"src": "ss1", "dest": "dd1"},
            ),
            copyfiles=(
                {"src": "ss2", "dest": "dd2"},
                {"src": "ss3", "dest": "dd3"},
            ),
        ),
        Project(name="dep2", path="dep2dir", url="https://git.example.com/base3/dep2.git"),
        Project(name="dep3", path="dep3", url="file:///repos/url1/sub.git", revision="main", groups=("test",)),
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
    assert manifest_spec.version == "1.0"
    assert not manifest_spec.remotes
    assert not manifest_spec.group_filters
    assert manifest_spec.defaults == Defaults()
    assert manifest_spec.dependencies == (
        ProjectSpec(name="dep1"),
        ProjectSpec(name="dep2"),
    )

    manifest = Manifest.from_spec(manifest_spec)
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="../dep1"),
        Project(name="dep2", path="dep2", url="../dep2"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(
        manifest_spec, refurl="https://my.domain.com/repos/main", path="foo", resolve_url=True
    )
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2"),
    )
    assert manifest.path == "foo"

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main", path="foo")
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="../dep1"),
        Project(name="dep2", path="dep2", url="../dep2"),
    )
    assert manifest.path == "foo"

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.git", resolve_url=True)
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1.git"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2.git"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.suffix", resolve_url=True)
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="https://my.domain.com/repos/dep1.suffix"),
        Project(name="dep2", path="dep2", url="https://my.domain.com/repos/dep2.suffix"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.suffix")
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", url="../dep1.suffix"),
        Project(name="dep2", path="dep2", url="../dep2.suffix"),
    )
    assert manifest.path is None


def test_remotes_unique():
    """Remote names must be unique."""
    with raises(ValueError):
        ManifestSpec(remotes=(Remote(name="foo", url_base="url"), Remote(name="foo", url_base="url")))
