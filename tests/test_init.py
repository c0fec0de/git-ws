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

"""Initialization Tests."""
from click.testing import CliRunner
from pytest import raises

from gitws import GitWS, InitializedError, ManifestExistError
from gitws._cli import main
from gitws.const import CONFIG_PATH, INFO_PATH

from .common import MANIFEST_DEFAULT
from .util import chdir, format_output, run


def test_cli_nogit(tmp_path):
    """Init without GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        result = CliRunner().invoke(main, ["init"])
    assert format_output(result) == [
        "Error: git clone has not been found or initialized yet. Change to your existing git clone or try:",
        "",
        "    git init",
        "",
        "or:",
        "",
        "    git clone",
        "",
        "",
    ]
    assert result.exit_code == 1


def test_cli_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 1
        assert format_output(result) == [
            "===== main =====",
            "Error: Manifest has not been found at 'git-ws.toml'. Try:",
            "",
            "    git ws manifest create --manifest='git-ws.toml'",
            "",
            "",
        ]

        result = CliRunner().invoke(main, ["manifest", "create"])
        assert format_output(result) == ["Manifest 'git-ws.toml' created.", ""]
        assert result.exit_code == 0

        manifest_path = main_path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        result = CliRunner().invoke(main, ["init"])
        assert format_output(result, tmp_path) == [
            "===== main =====",
            "Workspace initialized at '..'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]
        assert result.exit_code == 0

        result = CliRunner().invoke(main, ["init"])
        assert format_output(result, tmp_path) == [
            "===== main =====",
            "Error: git workspace has already been initialized at 'TMP' with main repo at 'main'.",
            "",
        ]
        assert result.exit_code == 1


def test_cli_git_update(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        result = CliRunner().invoke(main, ["manifest", "create"])
        assert format_output(result) == ["Manifest 'git-ws.toml' created.", ""]
        assert result.exit_code == 0

        manifest_path = main_path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        result = CliRunner().invoke(main, ["init", "--update"])
        assert format_output(result, tmp_path) == [
            "===== main =====",
            "Workspace initialized at '..'.",
            "",
        ]
        assert result.exit_code == 0


def test_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)

        GitWS.create_manifest()
        manifest_path = main_path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        with raises(ManifestExistError):
            GitWS.create_manifest()

        arepo = GitWS.init()

        assert arepo.path == tmp_path
        info_file = arepo.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
        ]
        config_file = arepo.path / CONFIG_PATH
        assert config_file.read_text().split("\n") == [
            'manifest_path = "git-ws.toml"',
            "",
        ]

        with raises(InitializedError):
            GitWS.init()

        rrepo = GitWS.from_path()
        assert arepo == rrepo
