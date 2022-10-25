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
from pytest import fixture

from gitws import Git, GitWS

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli


@fixture
def gws(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        gws = GitWS.clone(str(repos / "main"))
        gws.update(skip_main=True)

        yield gws


def test_status(tmp_path, gws):
    """Test status."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep1 = workspace / "dep1"
    dep2 = workspace / "dep2"

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status", "--branch")) == [
        "===== main (MAIN) =====",
        "## main...origin/main",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "## main...origin/main",
        "===== dep2 (revision='1-feature') =====",
        "## 1-feature...origin/1-feature",
        "===== dep4 (revision='main') =====",
        "## main...origin/main",
        "",
    ]

    (dep1 / "foo.txt").touch()
    (dep2 / "bb.txt").touch()
    (dep2 / "bc.txt").touch()

    assert cli(("status", "--branch")) == [
        "===== main (MAIN) =====",
        "## main...origin/main",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "## main...origin/main",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "## 1-feature...origin/1-feature",
        "?? dep2/bb.txt",
        "?? dep2/bc.txt",
        "===== dep4 (revision='main') =====",
        "## main...origin/main",
        "",
    ]

    assert cli(("status", "--branch", "dep2")) == [
        "===== dep2 (revision='1-feature') =====",
        "## 1-feature...origin/1-feature",
        "?? dep2/bb.txt",
        "?? dep2/bc.txt",
        "",
    ]

    assert cli(("status", "dep2/bc.txt")) == [
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/bc.txt",
        "",
    ]


def test_workflow(tmp_path, gws):
    """Test Full Workflow."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep1 = workspace / "dep1"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"
    git1 = Git(dep1)
    git2 = Git(dep2)
    git4 = Git(dep4)

    git1.set_config("user.email", "you@example.com")
    git1.set_config("user.name", "you")
    git2.set_config("user.email", "you@example.com")
    git2.set_config("user.name", "you")
    git4.set_config("user.email", "you@example.com")
    git4.set_config("user.name", "you")

    (dep1 / "foo.txt").touch()
    (dep2 / "bb.txt").touch()
    (dep4 / "foo.txt").touch()
    git4.add(("foo.txt",))

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    with chdir(dep1):
        assert cli(("status",)) == [
            "===== main (MAIN) =====",
            "===== dep1 =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "?? foo.txt",
            "===== dep2 (revision='1-feature') =====",
            "?? ../dep2/bb.txt",
            "===== dep4 (revision='main') =====",
            "A  ../dep4/foo.txt",
            "",
        ]

    assert cli(("add", "dep2/bb.txt", "dep1/foo.txt", "missing/file.txt"), exit_code=1) == [
        "Error: 'missing/file.txt' cannot be associated with any clone.",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("add", "dep2/bb.txt", "dep1/foo.txt")) == [""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "A  dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("commit", "dep2/bb.txt", "dep4/foo.txt"), exit_code=1) == [
        "Error: Please provide a commit message.",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "A  dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("commit", "dep2/bb.txt", "dep4/foo.txt", "-m", "messi")) == [
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status", "--branch")) == [
        "===== main (MAIN) =====",
        "## main...origin/main",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "## main...origin/main",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "## 1-feature...origin/1-feature [ahead 1]",
        "===== dep4 (revision='main') =====",
        "## main...origin/main [ahead 1]",
        "",
    ]

    assert cli(("reset", "dep1/foo.txt")) == [""]

    (dep2 / "barbar.txt").touch()

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("commit", "-m", "test")) == [""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status", "dep1")) == [
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "?? dep1/foo.txt",
        "",
    ]

    assert cli(("add", "dep1", "--all", "--force")) == [""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("commit", "-m", "changes")) == ["===== dep1 =====", ""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    (dep4 / "foo.txt").write_text("content")

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/foo.txt",
        "",
    ]

    assert cli(("commit", "-m", "files", "--all")) == ["===== dep4 (revision='main') =====", ""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("commit", "-m", "files", "--all")) == [""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("rm", "dep2/barbar.txt", "dep4/foo.txt"), exit_code=1) == [
        "Error: Command '['git', 'rm', '--', 'barbar.txt']' returned non-zero exit status 128.",
        "",
    ]

    assert cli(("rm",), exit_code=1) == ["Error: Nothing specified, nothing removed.", ""]

    assert cli(("rm", "dep4/foo.txt")) == [""]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "D  dep4/foo.txt",
        "",
    ]

    assert cli(("rm", "dep1/foo.txt", "--force", "--cached", "-r")) == [""]


def test_checkout_file(tmp_path, gws):
    """Checkout files."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Change")
    (dep4 / "data.txt").write_text("Other Change")

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout", "dep1/missing.txt"), exit_code=1) == [
        "===== dep1 =====",
        "Error: Command '['git', 'checkout', '--', 'missing.txt']' returned non-zero exit status 1.",
        "",
    ]

    assert cli(("checkout", "dep1/data.txt")) == [
        "===== dep1 =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout", "dep2/data.txt")) == [
        "===== dep2 (revision='1-feature') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]


def test_checkout(tmp_path, gws):
    """Checkout files."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Change")
    (dep4 / "data.txt").write_text("Other Change")

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout")) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout", "--force")) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_add(tmp_path, gws):
    """Add."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Change")
    (dep4 / "data.txt").write_text("Other Change")

    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]
    assert cli(("add",), exit_code=1) == [
        "Error: Nothing specified, nothing added.",
        "",
    ]
    assert cli(("add", "--all")) == [""]
    assert cli(("status",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "M  dep2/data.txt",
        "===== dep4 (revision='main') =====",
        "M  dep4/data.txt",
        "",
    ]


def test_diff(tmp_path, gws):
    """diff."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Text")
    (dep4 / "data.txt").write_text("Other Text")

    assert cli(("diff",)) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert cli(("diff", "dep2")) == [
        "===== dep2 (revision='1-feature') =====",
        "",
    ]

    assert cli(("diff", "--stat")) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        " dep2/data.txt | 2 +-",
        "===== dep4 (revision='main') =====",
        " dep4/data.txt | 2 +-",
        "",
    ]
    assert cli(("diff", "dep2", "--stat")) == [
        "===== dep2 (revision='1-feature') =====",
        " dep2/data.txt | 2 +-",
        "",
    ]

    with chdir(dep2):
        assert cli(("diff",)) == [
            "===== main (MAIN) =====",
            "===== dep1 =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "===== dep2 (revision='1-feature') =====",
            "===== dep4 (revision='main') =====",
            "",
        ]
        assert cli(("diff", "--stat")) == [
            "===== main (MAIN) =====",
            "===== dep1 =====",
            "git-ws WARNING Clone dep1 has no revision!",
            "===== dep2 (revision='1-feature') =====",
            " data.txt | 2 +-",
            "===== dep4 (revision='main') =====",
            " ../dep4/data.txt | 2 +-",
            "",
        ]
        assert cli(("diff", ".", "--stat")) == [
            "===== dep2 (revision='1-feature') =====",
            " data.txt | 2 +-",
            "",
        ]
