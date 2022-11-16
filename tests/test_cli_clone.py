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

from gitws.const import INFO_PATH

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, check, cli


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main")], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
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


def test_cli_clone_path(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        assert cli(["clone", str(repos / "main"), "main2"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main2 (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        check(workspace, "main", exists=False)
        check(workspace, "main2", content="main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        with chdir(workspace / "main2"):
            # Disable color here, to test normal error output
            assert cli(("config", "set", "color_ui", "False")) == [""]

            assert cli(["checkout"], tmp_path=tmp_path, repos_path=repos) == [
                "===== . (MAIN 'main2', revision='main') =====",
                "===== ../dep1 ('dep1') =====",
                "Cloning 'REPOS/dep1'.",
                "git-ws WARNING Clone dep1 has no revision!",
                "===== ../dep2 ('dep2', revision='1-feature') =====",
                "Cloning 'REPOS/dep2'.",
                "Already on '1-feature'",
                "===== ../dep4 ('dep4', revision='main') =====",
                "Cloning 'REPOS/dep4'.",
                "Already on 'main'",
                "",
            ]

        check(workspace, "main", exists=False)
        check(workspace, "main2", content="main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)


def test_cli_clone_long_path(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "some" / "where"

    with chdir(tmp_path):
        assert cli(
            ["clone", str(repos / "main"), "some/where/main", "--update"], tmp_path=tmp_path, repos_path=repos
        ) == [
            "===== some/where/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "===== some/where/dep1 ('dep1') =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "Cloning 'REPOS/dep1'.",
            "===== some/where/dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'REPOS/dep2'.",
            "===== some/where/dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]

        assert (
            workspace / INFO_PATH
        ).read_text() == '# Git Workspace System File. DO NOT EDIT.\n\nmain_path = "main"\n'

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)


def test_cli_clone_not_empty(tmp_path, repos):
    """Cloning via CLI not empty."""
    workspace = tmp_path / "main"
    workspace.mkdir()

    with chdir(tmp_path):
        (workspace / "file.txt").touch()
        assert cli(["clone", str(repos / "main")], exit_code=1) == [
            "Error: Workspace 'main' is not an empty directory.",
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

        assert cli(["clone", str(repos / "main"), "--force"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
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
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main"), "--update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "===== main/dep1 ('dep1') =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "Cloning 'REPOS/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'REPOS/dep2'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
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
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main")], tmp_path=tmp_path, repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
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
        assert cli(["checkout"], tmp_path=tmp_path, repos_path=repos) == [
            "===== . (MAIN 'main', revision='main') =====",
            "===== ../dep1 ('dep1') =====",
            "Cloning 'REPOS/dep1'.",
            "git-ws WARNING Clone dep1 has no revision!",
            "===== ../dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'REPOS/dep2'.",
            "Already on '1-feature'",
            "===== ../dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "Already on 'main'",
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
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main"), "-G", "+test"], repos_path=repos) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'REPOS/main'.",
            "Workspace initialized at 'main'. Please continue with:",
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

    assert (
        (workspace / ".git-ws" / "config.toml").read_text()
        == """\
manifest_path = "git-ws.toml"
group_filters = ["+test"]
"""
    )

    with chdir(workspace):
        assert cli(["update"], tmp_path=tmp_path, repos_path=repos) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Pulling branch 'main'.",
            "===== dep1 ('dep1') =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "Cloning 'REPOS/dep1'.",
            "===== dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'REPOS/dep2'.",
            "===== dep3 ('dep3', groups='test') =====",
            "git-ws WARNING Clone dep3 (groups='test') has no revision!",
            "Cloning 'REPOS/dep3'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Cloning 'REPOS/dep4'.",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)
