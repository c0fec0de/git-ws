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

"""Command Line Interface."""
from pathlib import Path

from gitws import ManifestSpec

from .util import chdir, cli


def test_cli_groupfilters_remote(tmp_path):
    """Group Filters."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("group-filters", "+myfoo, -myboo"))
        assert ManifestSpec.load(Path("git-ws.toml")).group_filters == ("+myfoo", "-myboo")

        cli(("group-filters", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).group_filters == tuple()
