# Copyright 2022-2025 c0fec0de
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

import tempfile
from pathlib import Path
from shutil import rmtree

from contextlib_chdir import chdir
from pytest import fixture

from gitws import Git, GitWS

from .fixtures import create_repos
from .util import cli, path2url


@fixture()
def repos():
    """Fixture with main and four dependency repos."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        create_repos(repos_path, add_dep5=True, add_dep6=True)

        yield repos_path


@fixture
def gws(tmp_path, repos):
    """Initialize :any:`GitWS` on ``repos``."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        gws.update(skip_main=True)

    with chdir(workspace):
        yield gws


def test_pull(tmp_path, gws):
    """Test pull."""
    _test_foreach(tmp_path, gws, "pull", on_branch=True)


def test_push(tmp_path, gws):
    """Test push."""
    dep6_sha = Git(gws.path / "dep6").get_sha()
    assert cli(("push",)) == [
        "===== dep4 ('dep4', revision='main') =====",
        f"===== SKIPPING dep6 ('dep6', revision='{dep6_sha}') =====",
        "===== SKIPPING dep5 ('dep5', revision='final2') =====",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== dep1 ('dep1') =====",
        "WARNING: Clone dep1 has no revision!",
        "===== main (MAIN 'main', revision='main') =====",
        "",
    ]


def test_fetch(tmp_path, gws):
    """Test fetch."""
    _test_foreach(tmp_path, gws, "fetch")


def test_rebase(tmp_path, gws):
    """Test rebase."""
    _test_foreach(tmp_path, gws, "rebase", on_branch=True)


def test_diff(tmp_path, gws):
    """Test diff."""
    _test_foreach(tmp_path, gws, "diff")


def test_deinit(tmp_path, gws):
    """Test deinit."""
    assert cli(["deinit"]) == ["Workspace deinitialized at '.'.", ""]

    assert not (tmp_path / "main" / ".gitws").exists()
    assert (tmp_path / "main" / "main").exists()
    assert (tmp_path / "main" / "dep1").exists()
    assert (tmp_path / "main" / "dep2").exists()
    assert not (tmp_path / "main" / "dep3").exists()
    assert (tmp_path / "main" / "dep4").exists()

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


def test_deinit_prune(tmp_path, gws):
    """Test deinit - prune."""
    assert cli(["deinit", "--prune"]) == [
        "===== dep1 (OBSOLETE) =====",
        "Removing 'dep1'.",
        "===== dep2 (OBSOLETE) =====",
        "Removing 'dep2'.",
        "===== dep4 (OBSOLETE) =====",
        "Removing 'dep4'.",
        "===== dep5 (OBSOLETE) =====",
        "Removing 'dep5'.",
        "===== dep6 (OBSOLETE) =====",
        "Removing 'dep6'.",
        "===== main (OBSOLETE) =====",
        "Removing 'main'.",
        "Workspace deinitialized at '.'.",
        "",
    ]

    assert not (tmp_path / "main" / ".gitws").exists()
    assert not (tmp_path / "main" / "main").exists()
    assert not (tmp_path / "main" / "dep1").exists()
    assert not (tmp_path / "main" / "dep2").exists()
    assert not (tmp_path / "main" / "dep3").exists()
    assert not (tmp_path / "main" / "dep4").exists()

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
    dep6_sha = Git(gws.path / "dep6").get_sha()
    assert cli(["git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "WARNING: Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== dep5 ('dep5', revision='final2') =====",
        f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]

    assert cli(["git", "status", "-P", "dep2", "-P", "./dep4"]) == [
        "===== SKIPPING main (MAIN 'main', revision='main') =====",
        "===== SKIPPING dep1 ('dep1') =====",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== SKIPPING dep5 ('dep5', revision='final2') =====",
        f"===== SKIPPING dep6 ('dep6', revision='{dep6_sha}') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]


def test_foreach(tmp_path, gws, repos):
    """Test foreach."""
    dep6_sha = Git(gws.path / "dep6").get_sha()
    assert cli(["foreach", "git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "WARNING: Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== dep5 ('dep5', revision='final2') =====",
        f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]


def test_foreach_clone_missing(tmp_path, gws):
    """Test foreach."""
    rmtree(tmp_path / "main" / "dep2")
    assert cli(["foreach", "git", "status"], exit_code=1) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "WARNING: Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "Error: Git Clone 'dep2' is missing. Try:",
        "",
        "    git ws update",
        "",
        "",
    ]


def test_foreach_fail(tmp_path, gws):
    """Test foreach failing."""
    assert cli(["foreach", "--", "git", "status", "--invalidoption"], exit_code=1) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Error: 'git status --invalidoption' failed.",
        "",
    ]


def test_outside(tmp_path, gws):
    """Outside Workspace."""
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


def _test_foreach(tmp_path, gws, *command, on_branch=False):
    dep6_sha = Git(gws.path / "dep6").get_sha()
    if on_branch:
        output = [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "===== SKIPPING dep5 ('dep5', revision='final2') =====",
            f"===== SKIPPING dep6 ('dep6', revision='{dep6_sha}') =====",
            "===== dep4 ('dep4', revision='main') =====",
            "",
        ]
    else:
        output = [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "===== dep5 ('dep5', revision='final2') =====",
            f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
            "===== dep4 ('dep4', revision='main') =====",
            "",
        ]
    assert cli(command) == output


def test_git_no_color(tmp_path, gws, repos):
    """Test git."""
    dep6_sha = Git(gws.path / "dep6").get_sha()
    assert cli(["config", "set", "color_ui", "False"]) == [""]
    assert cli(["git", "status"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "===== dep1 ('dep1') =====",
        "WARNING: Clone dep1 has no revision!",
        "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
        "===== dep5 ('dep5', revision='final2') =====",
        f"===== dep6 ('dep6', revision='{dep6_sha}') =====",
        "===== dep4 ('dep4', revision='main') =====",
        "",
    ]


def test_foreach_command_missing(tmp_path, gws):
    """Test git."""
    assert cli(["foreach"], exit_code=1) == ["Error: COMMAND is required", ""]
