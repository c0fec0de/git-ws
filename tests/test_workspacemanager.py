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

"""Workspace Manager Testing."""
from pytest import fixture

from gitws._util import relative
from gitws._workspacemanager import WorkspaceManager
from gitws.datamodel import FileRef
from gitws.workspace import Workspace

from .util import format_logs


@fixture()
def mgr(tmp_path):
    """Workspace with Manager."""
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir(parents=True, exist_ok=True)
    workspace = Workspace.init(workspace_path)
    yield WorkspaceManager(workspace)


def test_conflict(caplog, mgr, tmp_path):
    """Conflicting File References."""
    mgr.add(
        "bar",
        linkfiles=[
            FileRef(src="a.txt", dest="conflict.txt"),
            FileRef(src="b.txt", dest="conflict.txt"),
            FileRef(src="a.txt", dest="main-a.txt"),
        ],
        copyfiles=[FileRef(src="a.txt", dest="conflict.txt")],
    )
    mgr.add(
        "foo",
        linkfiles=[
            FileRef(src="a.txt", dest="conflict.txt"),
            FileRef(src="b.txt", dest="conflict.txt"),
            FileRef(src="a.txt", dest="main-a.txt"),
        ],
        copyfiles=[FileRef(src="a.txt", dest="conflict.txt")],
    )

    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "W"}) == [
        "ERROR   git-ws File 'W/conflict.txt' reference from 'W/bar/b.txt' already referenced from 'W/bar/a.txt'",
        "ERROR   git-ws File 'W/conflict.txt' reference from 'W/bar/a.txt' already referenced from 'W/bar/a.txt'",
        "ERROR   git-ws File 'W/conflict.txt' reference from 'W/foo/a.txt' already referenced from 'W/bar/a.txt'",
        "ERROR   git-ws File 'W/conflict.txt' reference from 'W/foo/b.txt' already referenced from 'W/bar/a.txt'",
        "ERROR   git-ws File 'W/main-a.txt' reference from 'W/foo/a.txt' already referenced from 'W/bar/a.txt'",
        "ERROR   git-ws File 'W/conflict.txt' reference from 'W/foo/a.txt' already referenced from 'W/bar/a.txt'",
    ]


def test_outside(caplog, mgr, tmp_path):
    """Try to escape workspace."""
    outside = tmp_path / "outside"
    mgr.add(
        "bar",
        linkfiles=[
            FileRef(src=str(outside / "src0.txt"), dest="dest0.txt"),
            FileRef(src="src1.txt", dest=str(outside / "dest0.txt")),
            FileRef(src="link.txt", dest="bar-link.txt"),
        ],
        copyfiles=[
            FileRef(src=str(outside / "src2.txt"), dest="dest2.txt"),
            FileRef(src="src3.txt", dest=str(outside / "dest3.txt")),
            FileRef(src="copy.txt", dest="bar-copy.txt"),
        ],
    )
    mgr.update()
    assert format_logs(
        caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "W", tmp_path / "workspace": "WS"}
    ) == [
        "ERROR   git-ws Cannot update: source 'TMP/outside/src0.txt' refers outside of workspace ('WS').",
        "ERROR   git-ws Cannot update: destination 'TMP/outside/dest0.txt' refers outside of workspace ('WS').",
        "ERROR   git-ws Cannot update: source file 'W/bar/link.txt' does not exists!",
        "ERROR   git-ws Cannot update: source 'TMP/outside/src2.txt' refers outside of workspace ('WS').",
        "ERROR   git-ws Cannot update: source file 'W/bar/src3.txt' does not exists!",
        "ERROR   git-ws Cannot update: source file 'W/bar/copy.txt' does not exists!",
    ]


def test_modified(caplog, mgr, tmp_path):
    """Modified Files."""
    workspace_path = mgr.workspace.path
    main_path = workspace_path / "main"
    main_path.mkdir(parents=True, exist_ok=True)
    (main_path / "link.txt").write_text("link")
    (main_path / "copy.txt").write_text("copy")
    mgr.add(
        "main",
        linkfiles=[
            FileRef(src="link.txt", dest="main-link.txt"),
        ],
        copyfiles=[
            FileRef(src="copy.txt", dest="main-copy.txt"),
        ],
    )
    mgr.update()
    assert (workspace_path / "main-link.txt").read_text() == "link"
    assert (workspace_path / "main-copy.txt").read_text() == "copy"

    # update source
    (main_path / "link.txt").write_text("link-update")
    (main_path / "copy.txt").write_text("copy-update")

    assert (workspace_path / "main-link.txt").read_text() == "link-update"
    assert (workspace_path / "main-copy.txt").read_text() == "copy"

    mgr.update()

    assert (workspace_path / "main-link.txt").read_text() == "link-update"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-update"

    # destroy dest
    (workspace_path / "main-link.txt").write_text("link-destroy")
    (workspace_path / "main-copy.txt").write_text("copy-destroy")

    assert (workspace_path / "main-link.txt").read_text() == "link-destroy"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-destroy"
    assert (main_path / "link.txt").read_text() == "link-destroy"
    assert (main_path / "copy.txt").read_text() == "copy-update"

    mgr.update()

    assert (workspace_path / "main-link.txt").read_text() == "link-destroy"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-destroy"

    # another source update
    (main_path / "link.txt").write_text("link-another-update")
    (main_path / "copy.txt").write_text("copy-another-update")
    assert (workspace_path / "main-link.txt").read_text() == "link-another-update"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-destroy"

    mgr.update()

    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: File 'WSREL/main/copy.txt' got "
        "manipulated. (Originally from 'WSREL/main-copy.txt')",
    ]

    assert (main_path / "link.txt").read_text() == "link-another-update"
    assert (main_path / "copy.txt").read_text() == "copy-another-update"
    assert (workspace_path / "main-link.txt").read_text() == "link-another-update"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-destroy"

    # Remove destroyed
    mgr.update(force=True)

    assert (main_path / "link.txt").read_text() == "link-another-update"
    assert (main_path / "copy.txt").read_text() == "copy-another-update"
    assert (workspace_path / "main-link.txt").read_text() == "link-another-update"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-another-update"

    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == []


def test_exists(caplog, mgr, tmp_path):
    """Test Existing Files."""
    workspace_path = mgr.workspace.path
    main_path = workspace_path / "main"
    main_path.mkdir(parents=True, exist_ok=True)
    (main_path / "link.txt").write_text("link")
    (main_path / "copy.txt").write_text("copy")
    mgr.add(
        "main",
        linkfiles=[
            FileRef(src="link.txt", dest="main-link.txt"),
        ],
        copyfiles=[
            FileRef(src="copy.txt", dest="main-copy.txt"),
        ],
    )
    (workspace_path / "main-link.txt").write_text("link-avail")
    (workspace_path / "main-copy.txt").write_text("copy-avail")

    mgr.update()

    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-link.txt' already exists!",
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-copy.txt' already exists!",
    ]

    assert (workspace_path / "main-link.txt").read_text() == "link-avail"
    assert (workspace_path / "main-copy.txt").read_text() == "copy-avail"

    mgr.update(force=True)

    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == []

    assert (workspace_path / "main-link.txt").read_text() == "link"
    assert (workspace_path / "main-copy.txt").read_text() == "copy"


def test_src_dir(caplog, mgr, tmp_path):
    """Source is Directory."""
    workspace_path = mgr.workspace.path
    main_path = workspace_path / "main"
    main_path.mkdir(parents=True, exist_ok=True)
    (main_path / "link.txt").mkdir()
    (main_path / "copy.txt").mkdir()
    mgr.add(
        "main",
        linkfiles=[
            FileRef(src="link.txt", dest="main-link.txt"),
        ],
        copyfiles=[
            FileRef(src="copy.txt", dest="main-copy.txt"),
        ],
    )
    mgr.update()
    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: source file 'WSREL/main/link.txt' is not a file!",
        "ERROR   git-ws Cannot update: source file 'WSREL/main/copy.txt' is not a file!",
    ]
    mgr.update(force=True)
    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: source file 'WSREL/main/link.txt' is not a file!",
        "ERROR   git-ws Cannot update: source file 'WSREL/main/copy.txt' is not a file!",
    ]


def test_dest_dir(caplog, mgr, tmp_path):
    """Destination is Directory."""
    workspace_path = mgr.workspace.path
    main_path = workspace_path / "main"
    main_path.mkdir(parents=True, exist_ok=True)
    (main_path / "link.txt").write_text("link")
    (main_path / "copy.txt").write_text("copy")
    (workspace_path / "main-link.txt").mkdir()
    (workspace_path / "main-copy.txt").mkdir()
    mgr.add(
        "main",
        linkfiles=[
            FileRef(src="link.txt", dest="main-link.txt"),
        ],
        copyfiles=[
            FileRef(src="copy.txt", dest="main-copy.txt"),
        ],
    )
    mgr.update()
    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-link.txt' already exists!",
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-copy.txt' already exists!",
    ]
    mgr.update(force=True)
    assert format_logs(caplog, tmp_path=tmp_path, replacements={relative(tmp_path / "workspace"): "WSREL"}) == [
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-link.txt' is not a file!",
        "ERROR   git-ws Cannot update: destination file 'WSREL/main-copy.txt' is not a file!",
    ]
