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

"""Manifest Format Testing."""

from pathlib import Path

from pytest import raises

from gitws import IncompatibleFormatError, ManifestFormat, ManifestSpec


def test_basic():
    """Basic Testing."""
    path = Path("git-ws.toml")
    manifest_format = ManifestFormat()
    assert not manifest_format.is_compatible(path)
    with raises(IncompatibleFormatError):
        manifest_format.load(path)
    with raises(IncompatibleFormatError):
        manifest_format.save(ManifestSpec(), path)
    with raises(IncompatibleFormatError):
        manifest_format.upgrade(path)
