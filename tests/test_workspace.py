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

"""Workspace Testing."""
from pathlib import Path

from pytest import raises

from gitws import InitializedError, OutsideWorkspaceError, UninitializedError
from gitws.const import CONFIG_PATH, INFO_PATH
from gitws.datamodel import FileRefType, WorkspaceFileRef
from gitws.workspace import Info, Workspace

from .common import TESTDATA_PATH
from .util import chdir


def test_load():
    """Test Load."""
    workspace_path = TESTDATA_PATH / "workspace0"
    workspace = Workspace.from_path(workspace_path / "bar" / "sub")
    assert workspace.path == workspace_path
    assert workspace.info == Info(main_path=Path("bar"))


def test_load_uninit(tmp_path):
    """Test Load Uninitialized."""
    with raises(UninitializedError):
        Workspace.from_path(tmp_path)


def test_init(tmp_path):
    """Initialize."""
    with chdir(tmp_path):
        main_path = tmp_path / "main"
        main_path.mkdir(parents=True)
        workspace = Workspace.init(tmp_path, main_path=main_path, manifest_path=Path("resolved.toml"))
        assert workspace.path == tmp_path
        assert workspace.info == Info(main_path=Path("main"))
        assert workspace.info.main_path == Path("main")
        info_file = workspace.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
        ]
        config_path = workspace.path / CONFIG_PATH
        assert config_path.read_text().split("\n") == [
            'manifest_path = "resolved.toml"',
            "",
        ]

        with raises(InitializedError):
            Workspace.init(tmp_path, main_path=main_path)


def test_outside(tmp_path):
    """Test Outside."""
    with chdir(tmp_path):
        sub_path = tmp_path / "sub"
        sub_path.mkdir(parents=True)
        with raises(OutsideWorkspaceError):
            Workspace.init(sub_path, main_path=tmp_path)


def test_edit_info(tmp_path):
    """Test Info Edit"""
    with chdir(tmp_path):
        main_path = tmp_path / "main"
        main_path.mkdir(parents=True)
        workspace = Workspace.init(tmp_path, main_path=main_path)
        info_file = workspace.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
        ]

        with workspace.edit_info() as info:
            info.filerefs.append(
                WorkspaceFileRef(type_=FileRefType.COPY.value, project_path="sub0/path", src="src0", dest="dest0")
            )
            info.filerefs.append(
                WorkspaceFileRef(type_=FileRefType.LINK.value, project_path="sub0/path", src="src0", dest="dest1")
            )
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
            "[[filerefs]]",
            'type_ = "copy"',
            'project_path = "sub0/path"',
            'src = "src0"',
            'dest = "dest0"',
            "",
            "[[filerefs]]",
            'type_ = "link"',
            'project_path = "sub0/path"',
            'src = "src0"',
            'dest = "dest1"',
            "",
        ]

        with workspace.edit_info() as info:
            info.filerefs.clear()
        assert info_file.read_text().split("\n") == [
            "# Git Workspace System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            "",
            "",
        ]
