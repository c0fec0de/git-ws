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

from gitws import Defaults, ManifestSpec

from .util import chdir, cli


def test_cli_default_remote(tmp_path):
    """Remote in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "remote", "myremote"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(remote="myremote")

        cli(("default", "remote", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults()


def test_cli_default_revision(tmp_path):
    """Revision in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "revision", "myrev"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(revision="myrev")

        cli(("default", "revision", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults()


def test_cli_default_groups(tmp_path):
    """groups in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "groups", "mygroup"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(groups=("mygroup",))

        cli(("default", "groups", "mygroup, myfoo"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(groups=("mygroup", "myfoo"))

        cli(("default", "groups", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults()


def test_cli_default_with_groups(tmp_path):
    """with_groups in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "with-groups", "mygroup"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(with_groups=("mygroup",))

        cli(("default", "with-groups", "mygroup, myfoo"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(with_groups=("mygroup", "myfoo"))

        cli(("default", "with-groups", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults()


def test_cli_default_submodules(tmp_path):
    """submodules in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "submodules", "true"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(submodules=True)

        cli(("default", "submodules", "false"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(submodules=False)


def test_cli_defaults(tmp_path):
    """Revision in defaults."""
    with chdir(tmp_path):
        cli(("manifest", "create"))

        cli(("default", "remote", "myremote"))
        cli(("default", "revision", "myrev"))
        cli(("default", "submodules", "false"))
        cli(("default", "groups", "foo,bar"))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(
            remote="myremote", revision="myrev", groups=("foo", "bar"), submodules=False
        )

        cli(("default", "revision", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(
            remote="myremote", groups=("foo", "bar"), submodules=False
        )

        cli(("default", "groups", ""))
        # cli(("default", "submodules", ""))
        assert ManifestSpec.load(Path("git-ws.toml")).defaults == Defaults(remote="myremote", submodules=False)
