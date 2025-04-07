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

"""Initialization Tests."""

from contextlib_chdir import chdir
from pytest import raises

from gitws import GitWS, InitializedError, ManifestExistError
from gitws.const import CONFIG_PATH, INFO_PATH

from .common import MANIFEST_DEFAULT
from .util import path2url, run


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
        assert gws.workspace == rrepo.workspace
        assert gws.manifest_path == rrepo.manifest_path
        assert gws.group_filters == rrepo.group_filters
        assert gws == rrepo


def test_from_path(tmp_path, repos):
    """From Path."""
    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        gws.update()

    workspace = tmp_path / "main"
    main_path = workspace / "main"
    dep1_path = workspace / "dep1"
    dep2_path = workspace / "dep2"

    gws = GitWS.from_path(path=workspace)
    assert gws.main_path == main_path
    assert gws.base_path == main_path

    gws = GitWS.from_path(path=main_path)
    assert gws.main_path == main_path
    assert gws.base_path == main_path

    gws = GitWS.from_path(path=dep1_path)
    assert gws.main_path == main_path
    assert gws.base_path == main_path

    gws = GitWS.from_path(path=dep2_path)
    assert gws.main_path == main_path
    assert gws.base_path == main_path


def test_reinit(tmp_path, repos):
    """Initialize."""
    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos / "main"))
        gws.update()

    workspace = tmp_path / "main"
    main_path = workspace / "main"
    dep1_path = workspace / "dep1"
    dep2_path = workspace / "dep2"

    info_file = workspace / INFO_PATH
    assert info_file.read_text().split("\n") == [
        "# Git Workspace System File. DO NOT EDIT.",
        "",
        'main_path = "main"',
        "",
    ]

    with raises(InitializedError):
        GitWS.init(main_path=main_path)

    with raises(InitializedError):
        GitWS.init(main_path=dep1_path)

    with raises(InitializedError):
        GitWS.init(main_path=dep2_path)

    # Re-Init
    GitWS.init(main_path=dep2_path, force=True)
    info_file = workspace / INFO_PATH
    assert info_file.read_text().split("\n") == [
        "# Git Workspace System File. DO NOT EDIT.",
        "",
        'main_path = "dep2"',
        "",
    ]

    assert GitWS.from_path(path=workspace).main_path == dep2_path
    assert GitWS.from_path(path=main_path).main_path == dep2_path
    assert GitWS.from_path(path=dep1_path).main_path == dep2_path
    assert GitWS.from_path(path=dep2_path).main_path == dep2_path
