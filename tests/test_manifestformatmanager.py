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

"""Manifest Format Manager Testing."""

from pathlib import Path

from pytest import raises

from gitws import AManifestFormat, IncompatibleFormat
from gitws._manifestformatmanager import ManifestFormatManager


def test_mngr(tmp_path):
    """Basic Testing"""
    mngr = ManifestFormatManager()
    filepath = tmp_path / "manifest.toml"
    with raises(IncompatibleFormat):
        with mngr.handle(filepath):
            pass


class OneFormat(AManifestFormat):

    """Just One Example Format."""

    prio: int = 1

    def is_compatible(self, path: Path) -> bool:
        """Check If File At ``path`` Is Compatible."""
        return path.suffix == ".one"


class AnotherOneFormat(OneFormat):

    """Another One Format."""


class TwoFormat(AManifestFormat):

    """Just Another Example Format."""

    prio: int = 1

    def is_compatible(self, path: Path) -> bool:
        """Check If File At ``path`` Is Compatible."""
        return path.suffix == ".two"


class AllFormat(AManifestFormat):

    """Default Format Handler."""

    def is_compatible(self, path: Path) -> bool:
        """Check If File At ``path`` Is Compatible."""
        return True


def test_prio():
    """Select By Prio."""
    mngr = ManifestFormatManager()
    one = OneFormat()
    mngr.add(one)
    aone = AnotherOneFormat()
    mngr.add(aone)
    all_ = AllFormat()
    mngr.add(all_)
    two = TwoFormat()
    mngr.add(two)

    with mngr.handle(Path("file.one")) as handler:
        assert handler is one
    with mngr.handle(Path("file.two")) as handler:
        assert handler is two
    with mngr.handle(Path("file.unknown")) as handler:
        assert handler is all_


def test_no_default():
    """Without Default."""

    mngr = ManifestFormatManager()
    one = OneFormat()
    mngr.add(one)
    aone = AnotherOneFormat()
    mngr.add(aone)
    two = TwoFormat()
    mngr.add(two)

    with mngr.handle(Path("file.one")) as handler:
        assert handler is one
    with mngr.handle(Path("file.two")) as handler:
        assert handler is two
    with raises(IncompatibleFormat):
        with mngr.handle(Path("file.unknown")) as handler:
            pass


def test_load_plugins():
    """Load Plugins."""
    mngr = ManifestFormatManager()
    mngr.load_plugins()
    assert any(format.__class__ for format in mngr.formats)
