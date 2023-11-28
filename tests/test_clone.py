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

"""Clone Testing."""
import os
from pathlib import Path
from shutil import rmtree
from unittest import mock

from pytest import raises

from gitws import Clone, Git, GitCloneNotCleanError, GitWS, Manifest, NotEmptyError, Project, WorkspaceNotEmptyError

from .util import chdir, check, path2url


def test_clone_basic():
    """Basic Tests."""
    project = Project(name="main", path="main", level=0, revision="main", is_main=True)
    git = Git(Path("main/main"))
    clone = Clone(project, git)

    assert clone.project is project
    assert clone.git is git

    ident = f"Clone({project!r}, {git!r})"
    assert str(clone) == ident
    assert repr(clone) == ident


def test_clone(tmp_path, repos):
    """Test Cloning."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        assert gws.path == workspace

        for clone in gws.clones():
            clone.check(exists=False)

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
            Project(name="main", path="main", level=0, revision="main", is_main=True),
            Project(name="dep1", path="dep1", level=1, url="../dep1"),
            Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
            Project(name="dep4", path="dep4", level=2, url="../dep4", revision="main"),
        ]
        assert list(gws.manifests()) == [
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep1", path="dep1", level=1, url="../dep1"),
                    Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
                    Project(name="dep3", path="dep3", level=1, url="../dep3", groups=("test",)),
                ),
                path=str(workspace / "main" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", level=1, url="../dep4", revision="main"),),
                path=str(workspace / "dep1" / "git-ws.toml"),
            ),
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep3", path="dep3", level=1, url="../dep3", revision="main", groups=("test",)),
                    Project(name="dep4", path="dep4", level=1, url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2" / "git-ws.toml"),
            ),
        ]
        assert list(gws.clones(resolve_url=False)) == [
            Clone(Project(name="main", path="main", level=0, revision="main", is_main=True), Git(Path("main/main"))),
            Clone(Project(name="dep1", path="dep1", level=1, url="../dep1"), Git(Path("main/dep1"))),
            Clone(
                Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
                Git(Path("main/dep2")),
            ),
            Clone(Project(name="dep4", path="dep4", level=2, url="../dep4", revision="main"), Git(Path("main/dep4"))),
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
            Project(name="main", path="main", level=0, revision="main", is_main=True),
            Project(name="dep1", path="dep1", level=1, url="../dep1"),
            Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
            Project(name="dep3", path="dep3", level=1, url="../dep3", groups=("test",)),
            Project(name="dep4", path="dep4", level=2, url="../dep4", revision="main"),
        ]
        assert list(gws.manifests()) == [
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep1", path="dep1", level=1, url="../dep1"),
                    Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
                    Project(name="dep3", path="dep3", level=1, url="../dep3", groups=("test",)),
                ),
                path=str(workspace / "main" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", level=1, url="../dep4", revision="main"),),
                path=str(workspace / "dep1" / "git-ws.toml"),
            ),
            Manifest(
                group_filters=("-test",),
                dependencies=(
                    Project(name="dep3", path="dep3", level=1, url="../dep3", revision="main", groups=("test",)),
                    Project(name="dep4", path="dep4", level=1, url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2" / "git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep2", path="dep2", level=1, url="../dep2"),),
                path=str(workspace / "dep3" / "git-ws.toml"),
            ),
        ]
        assert list(gws.clones(resolve_url=False)) == [
            Clone(Project(name="main", path="main", level=0, revision="main", is_main=True), Git(Path("main/main"))),
            Clone(Project(name="dep1", path="dep1", level=1, url="../dep1"), Git(Path("main/dep1"))),
            Clone(
                Project(name="dep2", path="dep2", level=1, url="../dep2", revision="1-feature", submodules=False),
                Git(Path("main/dep2")),
            ),
            Clone(Project(name="dep3", path="dep3", level=1, url="../dep3", groups=("test",)), Git(Path("main/dep3"))),
            Clone(Project(name="dep4", path="dep4", level=2, url="../dep4", revision="main"), Git(Path("main/dep4"))),
        ]


def test_clone_other(tmp_path, repos):
    """Test Clone Other."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        main_path = repos / "main"
        gws = GitWS.clone(str(main_path), manifest_path=Path("other.toml"))
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


def test_clone_cached(tmp_path, repos):
    """Test Cloning."""
    workspace = tmp_path / "main"
    cache = tmp_path / "cache"

    with mock.patch.dict(os.environ, {"GIT_WS_CLONE_CACHE": str(cache)}):
        with chdir(tmp_path):
            assert not cache.exists()

            gws = GitWS.clone(path2url(repos / "main"))
            assert gws.path == workspace

            gws.update()

            assert cache.exists()

            check(workspace, "main")
            check(workspace, "dep1")
            check(workspace, "dep2", content="dep2-feature")
            check(workspace, "dep3", exists=False)
            check(workspace, "dep4")
            check(workspace, "dep5", exists=False)

            rmtree(workspace / "dep1")
            rmtree(workspace / "dep2")

            gws.update()

            check(workspace, "main")
            check(workspace, "dep1")
            check(workspace, "dep2", content="dep2-feature")
            check(workspace, "dep3", exists=False)
            check(workspace, "dep4")
            check(workspace, "dep5", exists=False)

            # checkout too
            rmtree(workspace / "dep4")

            gws.checkout()

            check(workspace, "main")
            check(workspace, "dep1")
            check(workspace, "dep2", content="dep2-feature")
            check(workspace, "dep3", exists=False)
            check(workspace, "dep4")
            check(workspace, "dep5", exists=False)


def test_clone_force(tmp_path, repos):
    """Test Cloning - force."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        gws.update()

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        with raises(WorkspaceNotEmptyError):
            GitWS.clone(path2url(repos / "main"))

        with raises(NotEmptyError):
            GitWS.clone(path2url(repos / "main"), force=True)

        # remove main and one dep
        rmtree(workspace / "main")
        rmtree(workspace / "dep4")

        with raises(WorkspaceNotEmptyError):
            GitWS.clone(path2url(repos / "main"))

        gws = GitWS.clone(path2url(repos / "main"), force=True)

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        gws.update()

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)
