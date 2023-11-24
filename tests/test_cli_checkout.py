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

"""Command Line Interface - Update Variants."""

from gitws import GitWS

from .fixtures import create_repos
from .util import chdir, cli


def test_checkout(tmp_path):
    """Test update."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_path / "main"))
        gws.update(skip_main=True)

    with chdir(gws.path):
        assert cli(["status", "-bB"]) == [
            "===== main (MAIN 'main', revision='main') =====",
            "## main...origin/main",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "## main...origin/main",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "## 1-feature...origin/1-feature",
            "===== dep4 ('dep4', revision='main') =====",
            "## main...origin/main",
            "",
        ]

        assert cli(["checkout", "-b", "new-feature"]) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Switched to a new branch 'new-feature'",
            "WARNING: Clone main (MAIN revision='main') is on different revision: 'new-feature'",
            "===== dep1 ('dep1') =====",
            "Switched to a new branch 'new-feature'",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Switched to a new branch 'new-feature'",
            "WARNING: Clone dep2 (revision='1-feature', submodules=False) is on different revision: 'new-feature'",
            "===== dep4 ('dep4', revision='main') =====",
            "Switched to a new branch 'new-feature'",
            "WARNING: Clone dep4 (revision='main') is on different revision: 'new-feature'",
            "",
        ]

        assert cli(["dep", "update", "-r"]) == [""]

        assert cli(["status", "-bB"]) == [
            "===== main (MAIN 'main', revision='new-feature') =====",
            "## new-feature",
            " M main/git-ws.toml",
            "===== dep1 ('dep1', revision='new-feature') =====",
            "## new-feature",
            " M dep1/git-ws.toml",
            "===== dep2 ('dep2', revision='new-feature', submodules=False) =====",
            "## new-feature",
            " M dep2/git-ws.toml",
            "===== dep4 ('dep4', revision='new-feature') =====",
            "## new-feature",
            "",
        ]

        assert cli(["push", "--", "-u", "origin", "new-feature"]) == [
            "===== dep4 ('dep4', revision='new-feature') =====",
            "===== dep2 ('dep2', revision='new-feature', submodules=False) =====",
            "===== dep1 ('dep1', revision='new-feature') =====",
            "===== main (MAIN 'main', revision='new-feature') =====",
            "",
        ]
