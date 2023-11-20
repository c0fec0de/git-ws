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
from pydantic import ValidationError
from pytest import raises

from gitws import Defaults, FileRef, GroupSelect, MainFileRef, Manifest, ManifestSpec, Project, ProjectSpec, Remote

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
    with raises(ValidationError):
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
    with raises(ValidationError):
        defaults.remote = "other"

    with raises(ValueError):
        Defaults(groups=("-foo",))

    with raises(ValueError):
        Defaults(with_groups=("-foo",))


def test_fileref():
    """File Refs."""
    ref = FileRef(src="src0", dest="dest1")
    assert ref.src == "src0"
    assert ref.dest == "dest1"


def test_group_select():
    """Group Select."""
    group_select = GroupSelect(group="foo", select=True, path="path")
    assert group_select.group == "foo"
    assert group_select.select is True
    assert group_select.path == "path"
    assert str(group_select) == "+foo@path"

    # Immutable
    with raises(ValidationError):
        group_select.group = "blub"

    group_select = GroupSelect.from_group_filter("+foo@path")
    assert group_select.group == "foo"
    assert group_select.select is True
    assert group_select.path == "path"
    assert str(group_select) == "+foo@path"

    group_select = GroupSelect.from_group("foo")
    assert group_select.group == "foo"
    assert group_select.select is True
    assert group_select.path is None
    assert str(group_select) == "+foo"


def test_project():
    """Test ProjectSpec."""
    project = Project(name="name", path="path")
    assert project.name == "name"
    assert project.url is None
    assert project.revision is None
    assert project.manifest_path == "git-ws.toml"
    assert project.groups == tuple()
    assert project.with_groups == tuple()
    assert project.submodules is True
    assert project.linkfiles == tuple()
    assert project.copyfiles == tuple()
    assert project.info == "name (path='path')"

    # Immutable
    with raises(ValidationError):
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
    assert project.groups == ("a", "b")
    assert project.with_groups == ("c", "d")
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
    assert project_spec.groups == tuple()
    assert project_spec.with_groups == tuple()
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
    with raises(ValidationError):
        project_spec.name = "other"

    with raises(ValueError):
        ProjectSpec(name="name", groups=("-foo",))

    with raises(ValueError):
        ProjectSpec(name="name", with_groups=("-foo",))


def test_manifest():
    """Test Manifest."""
    manifest = Manifest()
    assert not manifest.group_filters
    assert not manifest.dependencies
    assert not manifest.linkfiles
    assert not manifest.copyfiles

    # Immutable
    with raises(ValidationError):
        manifest.defaults = Defaults()

    with raises(ValueError):
        Manifest(group_filters=("test",))


def test_manifest_spec():
    """Test ManifestSpec."""
    manifest_spec = ManifestSpec()
    assert manifest_spec.version == "1.0"
    assert manifest_spec.remotes == tuple()
    assert manifest_spec.group_filters == tuple()
    assert manifest_spec.defaults == Defaults()
    assert manifest_spec.linkfiles == tuple()
    assert manifest_spec.copyfiles == tuple()
    assert manifest_spec.dependencies == tuple()

    # Immutable
    with raises(ValidationError):
        manifest_spec.defaults = Defaults()

    with raises(ValueError):
        ManifestSpec(group_filters=("test",))


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
        "linkfiles": [
            {"src": "s0", "dest": "d0"},
            {"src": "s1", "dest": "d1", "groups": ["ab", "c"]},
        ],
        "copyfiles": [
            {"src": "c0", "dest": "e0"},
            {"src": "c1", "dest": "e1", "groups": ["ab", "c"]},
        ],
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
    assert manifest_spec.linkfiles == (
        MainFileRef(src="s0", dest="d0"),
        MainFileRef(src="s1", dest="d1", groups=("ab", "c")),
    )
    assert manifest_spec.copyfiles == (
        MainFileRef(src="c0", dest="e0"),
        MainFileRef(src="c1", dest="e1", groups=("ab", "c")),
    )


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
    project = Project.from_spec(manifest_spec, ProjectSpec(name="foo"), 0)
    assert project.name == "foo"
    assert project.url == "../foo"


def test_manifest_spec_missing_remote():
    """Determine ManifestSpec with missing Remote."""
    remotes = (Remote(name="remote2", url_base="foo"),)
    manifest_spec = ManifestSpec(remotes=remotes)
    with raises(ValueError) as exc:
        Project.from_spec(manifest_spec, ProjectSpec(name="foo", remote="remote1"), 0)
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
        "linkfiles": [
            {"src": "s0", "dest": "d0"},
            {"src": "s1", "dest": "d1", "groups": ["ab", "c"]},
        ],
        "copyfiles": [
            {"src": "c0", "dest": "e0"},
            {"src": "c1", "dest": "e1", "groups": ["ab", "c"]},
        ],
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
            level=1,
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
        Project(name="dep2", path="dep2dir", level=1, url="https://git.example.com/base3/dep2.git"),
        Project(name="dep3", path="dep3", level=1, url="file:///repos/url1/sub.git", revision="main", groups=("test",)),
    )
    assert manifest.path is None
    assert manifest.linkfiles == (
        MainFileRef(src="s0", dest="d0"),
        MainFileRef(src="s1", dest="d1", groups=("ab", "c")),
    )
    assert manifest.copyfiles == (
        MainFileRef(src="c0", dest="e0"),
        MainFileRef(src="c1", dest="e1", groups=("ab", "c")),
    )


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
        Project(name="dep1", path="dep1", level=1, url="../dep1"),
        Project(name="dep2", path="dep2", level=1, url="../dep2"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(
        manifest_spec, refurl="https://my.domain.com/repos/main", path="foo", resolve_url=True
    )
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", level=1, url="https://my.domain.com/repos/dep1"),
        Project(name="dep2", path="dep2", level=1, url="https://my.domain.com/repos/dep2"),
    )
    assert manifest.path == "foo"

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main", path="foo")
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", level=1, url="../dep1"),
        Project(name="dep2", path="dep2", level=1, url="../dep2"),
    )
    assert manifest.path == "foo"

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.git", resolve_url=True)
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", level=1, url="https://my.domain.com/repos/dep1.git"),
        Project(name="dep2", path="dep2", level=1, url="https://my.domain.com/repos/dep2.git"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.suffix", resolve_url=True)
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", level=1, url="https://my.domain.com/repos/dep1.suffix"),
        Project(name="dep2", path="dep2", level=1, url="https://my.domain.com/repos/dep2.suffix"),
    )
    assert manifest.path is None

    manifest = Manifest.from_spec(manifest_spec, refurl="https://my.domain.com/repos/main.suffix")
    assert not manifest.group_filters
    assert manifest.dependencies == (
        Project(name="dep1", path="dep1", level=1, url="../dep1.suffix"),
        Project(name="dep2", path="dep2", level=1, url="../dep2.suffix"),
    )
    assert manifest.path is None


def test_remotes_unique():
    """Remote names must be unique."""
    with raises(ValueError):
        ManifestSpec(remotes=(Remote(name="foo", url_base="url"), Remote(name="foo", url_base="url")))
