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

"""Clone Testing."""
from pytest import raises

from gitws import GitCloneNotCleanError, GitWS, Manifest, Project

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, check


def test_clone(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos / "main"))
        assert gws.path == workspace

        gws.update()
        assert gws.get_manifest().path == str(workspace / "main" / "git-ws.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        with chdir(workspace):
            rrepo = GitWS.from_path()
            assert gws == rrepo

        assert list(gws.projects()) == [
            Project(name="main", path="main", revision="main", is_main=True),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
        ]
        assert list(gws.manifests()) == [
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                    Project(name="dep3", path="dep3", url="../dep3", groups=("test",)),
                ),
                path=str(workspace / "main" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(workspace / "dep1" / "git-ws.toml"),
            ),
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=("test",)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2" / "git-ws.toml"),
            ),
        ]
        assert list(str(item) for item in gws.clones()) == [
            "Clone(Project(name='main', path='main', revision='main', is_main=True), Git(PosixPath('main/main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('main/dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', revision='1-feature'), "
            "Git(PosixPath('main/dep2')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('main/dep4')))",
        ]


def test_clone_groups(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "main"

    with chdir(tmp_path):
        main_path = repos / "main"
        gws = GitWS.clone(str(main_path), group_filters=("+test",))
        gws.update()
        assert gws.get_manifest().path == str(workspace / "main" / "git-ws.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        with chdir(workspace):
            rrepo = GitWS.from_path()
            assert gws == rrepo

        assert list(gws.projects()) == [
            Project(name="main", path="main", revision="main", is_main=True),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep3", path="dep3", url="../dep3", groups=("test",)),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
        ]
        assert list(gws.manifests()) == [
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                    Project(name="dep3", path="dep3", url="../dep3", groups=("test",)),
                ),
                path=str(workspace / "main" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(workspace / "dep1" / "git-ws.toml"),
            ),
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=("test",)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep2", path="dep2", url="../dep2"),),
                path=str(workspace / "dep3" / "git-ws.toml"),
            ),
        ]
        assert list(str(item) for item in gws.clones()) == [
            "Clone(Project(name='main', path='main', revision='main', is_main=True), Git(PosixPath('main/main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('main/dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', "
            "revision='1-feature'), Git(PosixPath('main/dep2')))",
            "Clone(Project(name='dep3', path='dep3', url='../dep3', groups=('test',)), Git(PosixPath('main/dep3')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('main/dep4')))",
        ]


def test_clone_other(tmp_path, repos):
    """Test Clone Other."""

    workspace = tmp_path / "main"

    with chdir(tmp_path):
        main_path = repos / "main"
        gws = GitWS.clone(str(main_path), manifest_path="other.toml")
        assert gws.path == workspace
        gws.update()
        assert gws.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        with chdir(workspace):
            rrepo = GitWS.from_path()
            assert gws == rrepo

        GitWS.from_path(manifest_path="git-ws.toml", path=workspace).update()
        assert gws.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        gws.update()

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        (workspace / "dep5").touch()
        (workspace / "dep2" / "file.txt").touch()

        with raises(GitCloneNotCleanError):
            gws.update(prune=True)

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        gws.update(prune=True, force=True)

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        assert gws.get_manifest().path == str(workspace / "main" / "other.toml")
