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

"""File Reference Updater."""

from gitws import FileRef
from gitws._filerefupdater import CopyFileUpdater, LinkFileUpdater
from gitws.datamodel import ProjectFileRefsMutable

from .util import format_logs


def test_linkfileupdater(tmp_path, caplog):
    """LinkFileUpdater."""
    path = tmp_path / "test"
    main_path = path / "main"
    main_path.mkdir(parents=True)
    existing: ProjectFileRefsMutable = {}
    lfu = LinkFileUpdater(path=path)
    (main_path / "file0.txt").write_text("main-file0")
    (main_path / "file1.txt").write_text("main-file1")
    main_filerefs = [FileRef(src="file0.txt", dest="main-file0.txt")]
    lfu.set("main", main_filerefs)
    lfu.remove(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    lfu.update(existing)
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").exists()
    lfu.set("main", [])
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").exists()
    lfu.remove(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    lfu.update(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    assert format_logs(caplog, tmp_path=tmp_path) == []


def test_linkfileupdater_outside(tmp_path, caplog):
    """LinkFileUpdater."""
    path = tmp_path / "test"
    main_path = path / "main"
    main_path.mkdir(parents=True)
    existing: ProjectFileRefsMutable = {}
    lfu = LinkFileUpdater(path=path)
    (main_path / "file0.txt").write_text("main-file0")
    main_filerefs = [FileRef(src="file0.txt", dest="../main-file0.txt")]
    lfu.set("main", main_filerefs)
    lfu.remove(existing)
    lfu.update(existing)
    assert format_logs(caplog, tmp_path=tmp_path) == [
        "ERROR   git-ws Cannot update symbolic link: destination 'TMP/main-file0.txt' "
        "is refers outside of workspace ('TMP/test').",
    ]


def test_copyfileupdater(tmp_path, caplog):
    """CopyFileUpdater."""
    path = tmp_path / "test"
    main_path = path / "main"
    main_path.mkdir(parents=True)
    existing: ProjectFileRefsMutable = {}
    lfu = CopyFileUpdater(path=path)
    (main_path / "file0.txt").write_text("main-file0")
    (main_path / "file1.txt").write_text("main-file1")
    main_filerefs = [FileRef(src="file0.txt", dest="main-file0.txt")]
    lfu.set("main", main_filerefs)
    lfu.remove(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    lfu.update(existing)
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").read_text() == "main-file0"
    lfu.update(existing)
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").read_text() == "main-file0"

    (main_path / "file0.txt").write_text("main-file0-modified")
    lfu.update(existing)
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").read_text() == "main-file0-modified"

    lfu.set("main", [])
    assert existing == {"main": main_filerefs}
    assert (path / "main-file0.txt").read_text() == "main-file0-modified"
    lfu.remove(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    lfu.update(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    assert format_logs(caplog, tmp_path=tmp_path) == []


def test_copyfileupdater_outside(tmp_path, caplog):
    """CopyFileUpdater."""
    path = tmp_path / "test"
    main_path = path / "main"
    main_path.mkdir(parents=True)
    existing: ProjectFileRefsMutable = {}
    lfu = CopyFileUpdater(path=path)
    (main_path / "file0.txt").write_text("main-file0")
    main_filerefs = [FileRef(src="file0.txt", dest="../main-file0.txt")]
    lfu.set("main", main_filerefs)
    lfu.remove(existing)
    lfu.update(existing)
    assert format_logs(caplog, tmp_path=tmp_path) == [
        "ERROR   git-ws Cannot update copied file: destination 'TMP/main-file0.txt' "
        "is refers outside of workspace ('TMP/test').",
    ]


def test_linkfileupdater_multiple(tmp_path, caplog):
    """LinkFileUpdater."""
    path = tmp_path / "test"
    main_path = path / "main"
    main_path.mkdir(parents=True)
    dep_path = path / "dep"
    dep_path.mkdir(parents=True)
    existing: ProjectFileRefsMutable = {}
    lfu = LinkFileUpdater(path=path)
    (main_path / "file0.txt").write_text("main-file0")
    (main_path / "file1.txt").write_text("main-file1")
    (dep_path / "file0.txt").write_text("dep-file0")
    (dep_path / "file1.txt").write_text("dep-file1")
    main_filerefs = [
        FileRef(src="file0.txt", dest="main-file0.txt"),
        FileRef(src="file1.txt", dest="sub/main-file1.txt"),
    ]
    dep_filerefs = [
        FileRef(src="file0.txt", dest="dep-file0.txt"),
        FileRef(src="file1.txt", dest="sub/dep-file1.txt"),
    ]
    lfu.set("main", main_filerefs)
    lfu.set("dep", dep_filerefs)
    lfu.remove(existing)
    lfu.update(existing)
    assert existing == {
        "main": main_filerefs,
        "dep": dep_filerefs,
    }
    assert (path / "main-file0.txt").read_text() == "main-file0"
    assert (path / "sub" / "main-file1.txt").read_text() == "main-file1"
    assert (path / "dep-file0.txt").read_text() == "dep-file0"
    assert (path / "sub" / "dep-file1.txt").read_text() == "dep-file1"

    main_filerefs = [
        FileRef(src="file0.txt", dest="main-file0.txt"),
    ]
    dep_filerefs = [
        FileRef(src="file1.txt", dest="sub/dep-file1.txt"),
    ]
    lfu.set("main", main_filerefs)
    lfu.set("dep", dep_filerefs)
    lfu.remove(existing)
    lfu.update(existing)
    assert existing == {
        "main": main_filerefs,
        "dep": dep_filerefs,
    }
    assert (path / "main-file0.txt").read_text() == "main-file0"
    assert not (path / "sub" / "main-file1.txt").exists()
    assert not (path / "dep-file0.txt").exists()
    assert (path / "sub" / "dep-file1.txt").read_text() == "dep-file1"

    lfu.set("main", [])
    lfu.set("dep", [])
    lfu.remove(existing)
    lfu.update(existing)
    assert not existing
    assert not (path / "main-file0.txt").exists()
    assert not (path / "sub" / "main-file1.txt").exists()
    assert not (path / "dep-file0.txt").exists()
    assert not (path / "sub" / "dep-file1.txt").exists()

    assert format_logs(caplog, tmp_path=tmp_path) == []
