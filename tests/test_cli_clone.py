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
# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, check, cli


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main")]) == [
            "===== main/main (MAIN 'main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
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
        assert cli(["clone", str(repos / "main"), "main2"]) == [
            "===== main2 (MAIN 'main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
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

        # Disable color here, to test normal error output
        assert cli(("config", "set", "color_ui", "False")) == [""]

        assert cli(["checkout"], tmp_path=tmp_path) == [
            "===== main2 (MAIN 'main2') =====",
            "===== dep1 ('dep1') =====",
            "Cloning 'TMP/repos/dep1'.",
            "git-ws WARNING Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'TMP/repos/dep2'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Cloning 'TMP/repos/dep4'.",
            "",
        ]

        check(workspace, "main", exists=False)
        check(workspace, "main2", content="main")
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

        assert cli(["clone", str(repos / "main"), "--force"], tmp_path=tmp_path) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'TMP/repos/main'.",
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
        assert cli(["clone", str(repos / "main"), "--update"]) == [
            "===== main/main (MAIN 'main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "===== main/dep1 ('dep1') =====",
            "git-ws WARNING Clone dep1 has no revision!",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== main/dep4 ('dep4', revision='main') =====",
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
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main")]) == [
            "===== main/main (MAIN 'main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
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
        assert cli(["checkout"], tmp_path=tmp_path) == [
            "===== . (MAIN 'main') =====",
            "===== ../dep1 ('dep1') =====",
            "Cloning 'TMP/repos/dep1'.",
            "git-ws WARNING Clone dep1 has no revision!",
            "===== ../dep2 ('dep2', revision='1-feature') =====",
            "Cloning 'TMP/repos/dep2'.",
            "===== ../dep4 ('dep4', revision='main') =====",
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
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        assert cli(["clone", str(repos / "main"), "-G", "+test"]) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning " f"'{tmp_path}/repos/main'.",
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
        assert cli(["update"]) == [
            "===== main (MAIN 'main') =====",
            "Pulling branch 'main'.",
            "===== dep1 ('dep1') =====",
            "git-ws WARNING Clone dep1 has no revision!",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== dep2 ('dep2', revision='1-feature') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== dep3 ('dep3', groups='test') =====",
            "git-ws WARNING Clone dep3 (groups='test') has no revision!",
            f"Cloning '{tmp_path}/repos/dep3'.",
            "===== dep4 ('dep4', revision='main') =====",
            f"Cloning '{tmp_path}/repos/dep4'.",
            "",
        ]

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)
