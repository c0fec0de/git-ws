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
from pytest import raises

from gitws import GitWS, InitializedError, ManifestExistError
from gitws.const import CONFIG_PATH, INFO_PATH

from .common import MANIFEST_DEFAULT
from .util import chdir, cli, run


def test_cli_nogit(tmp_path):
    """Init without GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        assert cli(["init"], exit_code=1) == [
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


def test_cli_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()
        assert not (tmp_path / ".git-ws").exists()

        assert cli(["init"], exit_code=1) == [
            "===== main (MAIN) =====",
            "Error: Manifest has not been found at 'git-ws.toml'. Try:",
            "",
            "    git ws manifest create --manifest='git-ws.toml'",
            "",
            "",
        ]

        assert not (tmp_path / ".git-ws").exists()

        assert cli(["manifest", "create"]) == ["Manifest 'git-ws.toml' created.", ""]

        manifest_path = main_path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        assert cli(["init"]) == [
            "===== main (MAIN) =====",
            "Workspace initialized at '..'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        assert cli(["init"], tmp_path=tmp_path, exit_code=1) == [
            "Error: git workspace has already been initialized at 'TMP' with main repo at 'main'.",
            "",
        ]


def test_cli_abs_manifest(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()
        assert not (tmp_path / ".git-ws").exists()
        assert cli(["manifest", "create"]) == ["Manifest 'git-ws.toml' created.", ""]

        assert cli(["init", "-M", str(main_path / "git-ws.toml")]) == [
            "===== main (MAIN) =====",
            "Workspace initialized at '..'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        assert cli(["init"], tmp_path=tmp_path, exit_code=1) == [
            "Error: git workspace has already been initialized at 'TMP' with main repo at 'main'.",
            "",
        ]


def test_cli_git_path(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()
        assert cli(["manifest", "create"]) == ["Manifest 'git-ws.toml' created.", ""]

    with chdir(tmp_path):
        assert cli(["init", "main", "add"], exit_code=1) == ["Error: more than one PATH specified", ""]

        assert cli(["init", "main"]) == [
            "===== main (MAIN) =====",
            "Workspace initialized at '.'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]

        assert cli(["checkout"]) == ["===== main (MAIN) =====", ""]

    assert (
        (tmp_path / ".git-ws" / "info.toml").read_text()
        == """\
# Git Workspace System File. DO NOT EDIT.

main_path = "main"
"""
    )
    assert (
        (tmp_path / ".git-ws" / "config.toml").read_text()
        == """\
manifest_path = "git-ws.toml"
"""
    )


def test_cli_init_exists(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()
        assert cli(["manifest", "create"]) == ["Manifest 'git-ws.toml' created.", ""]

        (tmp_path / "something").touch()

        assert cli(["init"], tmp_path=tmp_path, exit_code=1) == [
            "Error: Workspace '..' is not an empty directory.",
            "",
            "Choose an empty directory or use '--force'",
            "",
            "",
        ]

        assert not (tmp_path / ".git-ws").exists()
        assert cli(["init", "--force"], tmp_path=tmp_path) == [
            "===== main (MAIN) =====",
            "Workspace initialized at '..'.",
            "Please continue with:",
            "",
            "    git ws update",
            "",
            "",
        ]


def test_cli_git_update(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        assert cli(["manifest", "create"]) == ["Manifest 'git-ws.toml' created.", ""]

        manifest_path = main_path / "git-ws.toml"
        assert manifest_path.read_text() == MANIFEST_DEFAULT

        assert cli(["init", "--update"], tmp_path=tmp_path) == [
            "===== main (MAIN) =====",
            "Workspace initialized at '..'.",
            "",
        ]


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

        gws = GitWS.init()

        assert gws.path == tmp_path
        info_file = gws.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
        ]
        config_file = gws.path / CONFIG_PATH
        assert config_file.read_text().split("\n") == [
            'manifest_path = "git-ws.toml"',
            "",
        ]

        with raises(InitializedError):
            GitWS.init()

        rrepo = GitWS.from_path()
        assert rrepo.path == tmp_path
        assert gws == rrepo
