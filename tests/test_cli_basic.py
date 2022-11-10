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

"""Command Line Interface."""
from shutil import rmtree

from pytest import fixture

from gitws import GitWS

from .common import TESTDATA_PATH

# pylint: disable=unused-import
from .fixtures import repos
from .util import assert_gen, chdir, cli, format_logs


@fixture
def gws(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos / "main"))
        gws.update(skip_main=True)

    with chdir(workspace):
        yield gws


def test_pull(tmp_path, gws):
    """Test pull."""
    _test_foreach(tmp_path, gws, "pull")


def test_push(tmp_path, gws):
    """Test push."""
    # pylint: disable=unused-argument
    assert cli(("push",)) == [
        "===== dep4 ('dep4', revision='main') =====",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== main (MAIN 'main', revision='main') =====",
        "",
    ]


def test_fetch(tmp_path, gws):
    """Test fetch."""
    _test_foreach(tmp_path, gws, "fetch")


def test_rebase(tmp_path, gws):
    """Test rebase."""
    _test_foreach(tmp_path, gws, "rebase")


def test_diff(tmp_path, gws):
    """Test diff."""
    _test_foreach(tmp_path, gws, "diff")


def test_deinit(tmp_path, gws):
    """Test deinit."""
    # pylint: disable=unused-argument
    assert cli(["deinit"]) == ["Workspace deinitialized at '.'.", ""]

    assert not (tmp_path / "main/.gitws").exists()
    assert (tmp_path / "main/main").exists()

    assert cli(["deinit"], exit_code=1) == [
        "Error: git workspace has not been initialized yet. Try:",
        "",
        "    git ws init",
        "",
        "or:",
        "",
        "    git ws clone",
        "",
        "",
    ]


def test_git(tmp_path, gws):
    """Test git."""
    # pylint: disable=unused-argument
    assert cli(["git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]

    assert cli(["git", "status", "-P", "dep2", "-P", "./dep4"]) == [
        "===== SKIPPING main (MAIN 'main', revision='main') =====",
        "===== SKIPPING dep1 ('dep1') =====",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]


def test_foreach(tmp_path, gws, caplog, repos):
    """Test foreach."""
    # pylint: disable=unused-argument
    assert cli(["foreach", "git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]
    assert_gen(
        tmp_path / "gen", TESTDATA_PATH / "cli_basic" / "foreach", caplog=caplog, tmp_path=tmp_path, repos_path=repos
    )


def test_foreach_missing(tmp_path, gws, caplog):
    """Test foreach."""
    # pylint: disable=unused-argument
    rmtree(tmp_path / "main" / "dep2")
    assert cli(["foreach", "git", "status"], exit_code=1) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "Error: Git Clone 'dep2' is missing. Try:",
        "",
        "    git ws update",
        "",
        "",
    ]


def test_foreach_fail(tmp_path, gws):
    """Test foreach failing."""
    # pylint: disable=unused-argument
    assert cli(["foreach", "--", "git", "status", "--invalidoption"], exit_code=1) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Error: 'git status --invalidoption' failed.",
        "",
    ]


def test_outside(tmp_path, gws):
    """Outside Workspace."""
    # pylint: disable=unused-argument
    with chdir(tmp_path):
        assert cli(["update"], exit_code=1) == [
            "Error: git workspace has not been initialized yet. Try:",
            "",
            "    git ws init",
            "",
            "or:",
            "",
            "    git ws clone",
            "",
            "",
        ]


def _test_foreach(tmp_path, gws, *command):
    # pylint: disable=unused-argument
    assert cli(command) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]


def test_git_no_color(tmp_path, gws, caplog, repos):
    """Test git."""
    # pylint: disable=unused-argument
    assert cli(["config", "set", "color_ui", "False"]) == [""]
    assert cli(["git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]
    assert_gen(
        tmp_path / "gen",
        TESTDATA_PATH / "cli_basic" / "git_no_color",
        caplog=caplog,
        tmp_path=tmp_path,
        repos_path=repos,
    )
