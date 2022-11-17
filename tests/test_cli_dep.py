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

"""Command Line Interface."""
from pathlib import Path

from gitws import ManifestSpec, ProjectSpec

from .util import chdir, cli


def test_cli_dep(tmp_path):
    """Add, List, Delete Dependencies."""
    with chdir(tmp_path):
        cli(("manifest", "create"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == tuple()

        cli(("dep", "add", "dep1"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == (ProjectSpec(name="dep1"),)

        assert cli(("dep", "add", "dep1"), exit_code=1) == [
            "Error: 1 validation error for ManifestSpec",
            "__root__",
            "  Dependency name 'dep1' is used more than once (type=value_error)",
            "",
        ]

        assert cli(
            (
                "dep",
                "add",
                "dep2",
                "--remote",
                "remote",
                "--sub-url",
                "sub-url",
                "--revision",
                "revision",
                "--path",
                "path",
                "--dep-manifest-path",
                "dep-manifest-path",
                "--groups",
                "c,d",
                "--with-groups",
                "a, b",
                "--submodules",
                "false",
            )
        )
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == (
            ProjectSpec(name="dep1"),
            ProjectSpec(
                name="dep2",
                remote="remote",
                sub_url="sub-url",
                revision="revision",
                path="path",
                manifest_path="dep-manifest-path",
                groups=("c", "d"),
                with_groups=("a", "b"),
                submodules=False,
            ),
        )

        cli(("dep", "set", "dep1", "url", "myurl.git"))

        assert cli(("dep", "set", "dep3", "url", "myurl.git"), exit_code=1) == ["Error: Unknown dependency 'dep3'", ""]

        assert cli(("dep", "list")) == [
            "[[dependencies]]",
            'name = "dep1"',
            'url = "myurl.git"',
            "",
            "[[dependencies]]",
            'name = "dep2"',
            'remote = "remote"',
            'sub-url = "sub-url"',
            'revision = "revision"',
            'path = "path"',
            'manifest-path = "dep-manifest-path"',
            'groups = ["c", "d"]',
            'with-groups = ["a", "b"]',
            "submodules = false",
            "",
            "",
        ]

        cli(("dep", "delete", "dep2"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == (ProjectSpec(name="dep1", url="myurl.git"),)

        assert cli(("dep", "list")) == ["[[dependencies]]", 'name = "dep1"', 'url = "myurl.git"', "", ""]

        cli(("dep", "delete", "dep1"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == tuple()

        assert cli(("dep", "delete", "dep3"), exit_code=1) == ["Error: Unknown dependency 'dep3'", ""]
