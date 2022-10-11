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
from gitws import GitWS, Group, Manifest, Project

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli


def check(workspace, name, content=None, exists=True):
    """Check."""
    file_path = workspace / name / "data.txt"
    content = content or name
    if exists:
        assert file_path.exists()
        assert file_path.read_text() == f"{content}"
    else:
        assert not file_path.exists()


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        assert cli(["clone", str(repos / "main")]) == [
            "===== main =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)


def test_cli_clone_not_empty(tmp_path, repos):
    """Cloning via CLI not empty."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        (workspace / "file.txt").touch()
        assert cli(["clone", str(repos / "main")], exit_code=1) == [
            "Error: Workspace '.' is not an empty directory.",
            "",
            "Choose an empty directory or use '--force'",
            "",
            "",
        ]

        check(workspace, "main", exists=False)
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        assert cli(["clone", str(repos / "main"), "--force"], tmp_path=tmp_path) == [
            "===== main =====",
            "Cloning 'TMP/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)


def test_cli_clone_update(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        assert cli(["clone", str(repos / "main"), "--update"]) == [
            "===== main =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "===== dep1 =====",
            "git-ws WARNING Clone dep1 has an empty revision!",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== dep2 (revision='1-feature') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== dep4 (revision='main') =====",
            f"Cloning '{tmp_path}/repos/dep4'.",
            "",
        ]

    check(workspace, "main")
    check(workspace, "dep1")
    check(workspace, "dep2", content="dep2-feature")
    check(workspace, "dep3", exists=False)
    check(workspace, "dep4")
    check(workspace, "dep5", exists=False)


def test_cli_clone_checkout(tmp_path, repos):
    """Cloning via CLI and checkout."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        assert cli(["clone", str(repos / "main")]) == [
            "===== main =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

    with chdir(workspace / "main"):
        assert cli(["checkout"], tmp_path=tmp_path) == [
            "===== main =====",
            "===== dep1 =====",
            "Cloning 'TMP/repos/dep1'.",
            "===== dep2 (revision='1-feature') =====",
            "Cloning 'TMP/repos/dep2'.",
            "===== dep4 (revision='main') =====",
            "Cloning 'TMP/repos/dep4'.",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)


def test_cli_clone_groups(tmp_path, repos):
    """Cloning via CLI with groups."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        assert cli(["clone", str(repos / "main"), "-G", "+test"]) == [
            "===== main =====",
            "Cloning " f"'{tmp_path}/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        assert cli(["update"]) == [
            "Groups: '+test'",
            "===== main =====",
            "Pulling branch 'main'.",
            "===== dep1 =====",
            "git-ws WARNING Clone dep1 has an empty revision!",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== dep2 (revision='1-feature') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== dep4 (revision='main') =====",
            f"Cloning '{tmp_path}/repos/dep4'.",
            "===== dep3 (revision='main', groups='test') =====",
            f"Cloning '{tmp_path}/repos/dep3'.",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)


def test_clone(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = GitWS.clone(str(main_path))
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "git-ws.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        rrepo = GitWS.from_path()
        assert arepo == rrepo

        assert list(arepo.projects()) == [
            Project(name="main", path="main", is_main=True),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
        ]
        assert list(arepo.manifests()) == [
            Manifest(
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                ),
                path=str(tmp_path / "workspace/main/git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(tmp_path / "workspace/dep1/git-ws.toml"),
            ),
            Manifest(
                groups=(Group(name="test"),),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=(Group(name="test"),)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(tmp_path / "workspace/dep2/git-ws.toml"),
            ),
        ]
        assert list(str(item) for item in arepo.clones()) == [
            "Clone(Project(name='main', path='main', is_main=True), Git(PosixPath('main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', revision='1-feature'), Git(PosixPath('dep2')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('dep4')))",
        ]


def test_clone_groups(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = GitWS.clone(str(main_path), groups="+test")
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "git-ws.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        rrepo = GitWS.from_path()
        assert arepo == rrepo

        assert list(arepo.projects()) == [
            Project(name="main", path="main", is_main=True),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
            Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=(Group(name="test"),)),
        ]
        assert list(arepo.projects(filter_=lambda project: not project.is_main)) == [
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
            Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=(Group(name="test"),)),
        ]
        assert list(arepo.manifests()) == [
            Manifest(
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                ),
                path=str(tmp_path / "workspace/main/git-ws.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(tmp_path / "workspace/dep1/git-ws.toml"),
            ),
            Manifest(
                groups=(Group(name="test"),),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", revision="main", groups=(Group(name="test"),)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(tmp_path / "workspace/dep2/git-ws.toml"),
            ),
        ]
        assert list(str(item) for item in arepo.clones()) == [
            "Clone(Project(name='main', path='main', is_main=True), Git(PosixPath('main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', revision='1-feature'), Git(PosixPath('dep2')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('dep4')))",
            "Clone(Project(name='dep3', path='dep3', url='../dep3', revision='main', "
            "groups=(Group(name='test'),)), Git(PosixPath('dep3')))",
        ]

        assert list(arepo.projects(manifest_path="missing.toml")) == [Project(name="main", path="main", is_main=True)]
        assert not list(arepo.manifests(manifest_path="missing.toml"))


def test_clone_other(tmp_path, repos):
    """Test Clone Other."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = GitWS.clone(str(main_path), manifest_path="other.toml")
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        rrepo = GitWS.from_path()
        assert arepo == rrepo

        arepo.update(manifest_path="git-ws.toml")
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        assert cli(("update",)) == [
            "===== main =====",
            "Pulling branch 'main'.",
            "===== dep1 (revision='main') =====",
            "Pulling branch 'main'.",
            "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
            "Pulling branch 'main'.",
            "===== dep4 (revision='4-feature') =====",
            "Fetching.",
            "Checking out '4-feature' (previously 'main').",
            "Merging branch '4-feature'.",
            "",
        ]

        # Disable color here, to test normal error output
        assert cli(("config", "set", "color_ui", "False")) == [""]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        (workspace / "dep5").touch()

        assert cli(("update", "--prune"), exit_code=1) == [
            "===== main =====",
            "Pulling branch 'main'.",
            "===== dep1 (revision='main') =====",
            "Pulling branch 'main'.",
            "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
            "Pulling branch 'main'.",
            "===== dep4 (revision='4-feature') =====",
            "Pulling branch '4-feature'.",
            "===== dep2 (OBSOLETE) =====",
            "Removing 'dep2'.",
            "Error: Git Clone 'dep2' contains changes.",
            "",
            "Commit/Push all your changes and branches or use '--force'",
            "",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        assert cli(("update", "--prune", "--force")) == [
            "===== main =====",
            "Pulling branch 'main'.",
            "===== dep1 (revision='main') =====",
            "Pulling branch 'main'.",
            "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
            "Pulling branch 'main'.",
            "===== dep4 (revision='4-feature') =====",
            "Pulling branch '4-feature'.",
            "===== dep2 (OBSOLETE) =====",
            "Removing 'dep2'.",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")
