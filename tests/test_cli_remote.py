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

from gitws import ManifestSpec, Remote

from .util import chdir, cli


def test_cli_remote(tmp_path):
    """Add, List, Delete Remote."""
    with chdir(tmp_path):
        cli(("manifest", "create"))
        assert ManifestSpec.load(Path("git-ws.toml")).remotes == tuple()

        cli(("remote", "add", "myremote", "myurl"))
        assert ManifestSpec.load(Path("git-ws.toml")).remotes == (Remote(name="myremote", url_base="myurl"),)

        cli(("remote", "add", "myremote2", "myurl2"))
        assert ManifestSpec.load(Path("git-ws.toml")).remotes == (
            Remote(name="myremote", url_base="myurl"),
            Remote(name="myremote2", url_base="myurl2"),
        )

        assert cli(("remote", "list")) == ["myremote: myurl", "myremote2: myurl2", ""]

        cli(("remote", "delete", "myremote2"))
        assert ManifestSpec.load(Path("git-ws.toml")).remotes == (Remote(name="myremote", url_base="myurl"),)

        assert cli(("remote", "list")) == ["myremote: myurl", ""]

        cli(("remote", "delete", "myremote"))
        assert ManifestSpec.load(Path("git-ws.toml")).remotes == tuple()

        assert cli(("remote", "delete", "myremote3"), exit_code=1) == ["Error: Unknown dependency 'myremote3'", ""]
