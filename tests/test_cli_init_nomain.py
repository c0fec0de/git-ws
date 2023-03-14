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

"""Initialization Tests without Main Repo."""
from gitws.const import CONFIG_PATH, INFO_PATH

from .util import chdir, cli


def test_nomain(tmp_path):
    """Init without main."""
    path = tmp_path / "workspace"
    path.mkdir(parents=True)
    with chdir(path):
        assert cli(("manifest", "create")) == ["Manifest 'git-ws.toml' created.", ""]

        assert cli(("init", "--update")) == ["Workspace initialized at '.'.", ""]

        info_file = path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            "",
        ]
        config_file = path / CONFIG_PATH
        assert config_file.read_text().split("\n") == [
            'manifest_path = "git-ws.toml"',
            "",
        ]

        assert cli(("init",), exit_code=1, tmp_path=tmp_path) == [
            "Error: git workspace has already been initialized at 'TMP/workspace'.",
            "",
        ]

        assert cli(("init", "--force", "--group-filter=+test", "--group-filter=-doc")) == [
            "Workspace initialized at '.'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        assert cli(("info", "main-path"), exit_code=1) == [
            "Error: Workspace has been initialized from manifest only, without a main project.",
            "",
        ]
