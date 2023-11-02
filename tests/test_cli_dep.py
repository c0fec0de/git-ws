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

from gitws import Git, ManifestSpec, ProjectSpec

from .fixtures import create_repos
from .util import chdir, cli, path2url


def test_cli_dep(tmp_path):
    """Add, List, Delete Dependencies."""
    with chdir(tmp_path):
        cli(("manifest", "create"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == tuple()

        cli(("dep", "add", "dep1"))
        assert ManifestSpec.load(Path("git-ws.toml")).dependencies == (ProjectSpec(name="dep1"),)

        assert cli(("dep", "add", "dep1"), exit_code=1)

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

        assert cli(("dep", "set", "dep4", "url", "myurl.git"), exit_code=1) == ["Error: Unknown dependency 'dep4'", ""]

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


def _get_revisions(workspace_path):
    for manifest_path in sorted(workspace_path.glob("*/git-ws.toml")):

        name = manifest_path.parent.name
        manifest_spec = ManifestSpec.load(manifest_path)
        revisions = {project_spec.name: project_spec.revision for project_spec in manifest_spec.dependencies}
        yield name, revisions


def test_cli_dep_update_revision(tmp_path):
    """Test Update Revision."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path, add_dep5=True)
    workspace_path = tmp_path / "main"
    with chdir(tmp_path):
        assert cli(["clone", path2url(repos_path / "main"), "--update"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/main'.",
            "===== main/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'file://REPOS/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'file://REPOS/dep2'.",
            "===== main/dep5 ('dep5', revision='final2') =====",
            "Cloning 'file://REPOS/dep5'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'file://REPOS/dep4'.",
            "",
        ]

    with chdir(workspace_path):
        assert tuple(_get_revisions(workspace_path)) == (
            ("dep1", {"dep4": "main"}),
            ("dep2", {"dep3": None, "dep4": "main"}),
            ("main", {"dep1": None, "dep2": "1-feature", "dep3": None, "dep5": "final2"}),
        )

        Git(workspace_path / "dep2").checkout("main")
        Git(workspace_path / "dep4").checkout("4-feature")

        for _ in range(2):
            assert cli(["dep", "update", "revision"], tmp_path=tmp_path) == [""]
            assert tuple(_get_revisions(workspace_path)) == (
                ("dep1", {"dep4": "main"}),
                ("dep2", {"dep3": None, "dep4": "main"}),
                ("main", {"dep1": "main", "dep2": "main", "dep3": None, "dep5": "final2"}),
            )

        for _ in range(2):
            assert cli(["dep", "update", "revision", "--recursive"], tmp_path=tmp_path) == [""]
            assert tuple(_get_revisions(workspace_path)) == (
                ("dep1", {"dep4": "4-feature"}),
                ("dep2", {"dep3": None, "dep4": "main"}),
                ("main", {"dep1": "main", "dep2": "main", "dep3": None, "dep5": "final2"}),
            )
