# Copyright 2023 c0fec0de
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

"""Utility Testing."""

from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

from gitws._pathlock import atomic_update_or_create_path, path_lock


def test_path_lock():
    """Test the path locking utility."""
    with TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "hello.md"
        with path_lock(path):
            sleep(2)
            path.write_text("Hello World!", encoding="utf-8")


def test_atomic_updates_on_file():
    """Test if atomic file updates work."""
    with TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "test.txt"

        with atomic_update_or_create_path(path) as tmp_path:
            assert not tmp_path.exists()
            tmp_path.write_text("Hello World", encoding="utf-8")
        assert path.read_text(encoding="utf-8") == "Hello World"

        with atomic_update_or_create_path(path) as tmp_path:
            assert tmp_path.exists()
            assert tmp_path.is_file()
            tmp_path.write_text("Updated Hello World", encoding="utf-8")
        assert path.read_text(encoding="utf-8") == "Updated Hello World"


def test_atomic_updates_on_directory():
    """Test if atomic directory updates work."""
    with TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "folder"

        with atomic_update_or_create_path(path) as tmp_path:
            assert not tmp_path.exists()
            tmp_path.mkdir(parents=True)
            (tmp_path / "hello.txt").write_text("Hello World", encoding="utf-8")
        assert (path / "hello.txt").read_text(encoding="utf-8") == "Hello World"

        with atomic_update_or_create_path(path) as tmp_path:
            assert tmp_path.exists()
            assert tmp_path.is_dir()
            (tmp_path / "hello.txt").write_text("Updated Hello World", encoding="utf-8")
        assert (path / "hello.txt").read_text(encoding="utf-8") == "Updated Hello World"


def test_atomic_create_without_input():
    """Test if using the atomic create works if no file or folder is created."""
    with TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "test.txt"

        with atomic_update_or_create_path(path):
            # Do nothing - we don't create a new file/folder and hence, this
            # is a no-op. Still, the function should not throw any error on
            # this.
            pass

        assert not path.exists()
