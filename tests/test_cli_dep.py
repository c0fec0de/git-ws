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

from pytest import fixture

from gitws import Git, ManifestSpec, ProjectSpec
from gitws._util import run

from .fixtures import create_repos, git_repo
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


def _get_infos(workspace_path):
    for manifest_path in sorted(workspace_path.glob("*/git-ws.toml")):

        name = manifest_path.parent.name
        manifest_spec = ManifestSpec.load(manifest_path)
        revisions = [
            (project_spec.name, project_spec.revision, project_spec.url) for project_spec in manifest_spec.dependencies
        ]
        yield name, revisions


@fixture
def workspace_path(tmp_path):
    """Workspace and Repos."""
    repos_path = tmp_path / "repos"
    for sub_path in (repos_path / "one", repos_path / "two"):
        create_repos(sub_path, add_dep5=True)

    with chdir(tmp_path):
        assert cli(
            ["clone", path2url(repos_path / "one" / "main"), "--update", "-G", "+test"],
            tmp_path=tmp_path,
            repos_path=repos_path,
        ) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/one/main'.",
            "===== main/dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Cloning 'file://REPOS/one/dep1'.",
            "===== main/dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Cloning 'file://REPOS/one/dep2'.",
            "===== main/dep3 ('dep3', groups='test') =====",
            "WARNING: Clone dep3 (groups='test') has no revision!",
            "Cloning 'file://REPOS/one/dep3'.",
            "===== main/dep5 ('dep5', revision='final2') =====",
            "Cloning 'file://REPOS/one/dep5'.",
            "===== main/dep4 ('dep4', revision='main') =====",
            "Cloning 'file://REPOS/one/dep4'.",
            "",
        ]

    workspace_path = tmp_path / "main"
    with chdir(workspace_path):
        yield workspace_path


def test_cli_dep_update(tmp_path, workspace_path):
    """Test Update."""
    repos_path = workspace_path.parent / "repos"
    assert tuple(_get_infos(workspace_path)) == (
        ("dep1", [("dep4", "main", "../dep4")]),
        ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
        ("dep3", [("dep2", None, "../dep2")]),
        (
            "main",
            [
                ("dep1", None, "../dep1"),
                ("dep2", "1-feature", "../dep2"),
                ("dep3", None, None),
                ("dep5", "final2", None),
            ],
        ),
    )
    Git(workspace_path / "dep2").checkout("main")
    run(["git", "remote", "set-url", "origin", path2url(repos_path / "two" / "dep1")], cwd=workspace_path / "dep1")
    Git(workspace_path / "dep4").checkout("4-feature")

    for _ in range(2):
        assert cli(["dep", "update"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "main", "../dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", "main", "../../two/dep1"),
                    ("dep2", "main", None),
                    ("dep3", "main", None),
                    ("dep5", "final2", None),
                ],
            ),
        )

    for _ in range(2):
        assert cli(["dep", "update", "--recursive"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "4-feature", "../../one/dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", "main", "../../two/dep1"),
                    ("dep2", "main", None),
                    ("dep3", "main", None),
                    ("dep5", "final2", None),
                ],
            ),
        )


def test_cli_dep_update_revision(tmp_path, workspace_path):
    """Test Update Revision."""
    repos_path = workspace_path.parent / "repos"
    assert tuple(_get_infos(workspace_path)) == (
        ("dep1", [("dep4", "main", "../dep4")]),
        ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
        ("dep3", [("dep2", None, "../dep2")]),
        (
            "main",
            [
                ("dep1", None, "../dep1"),
                ("dep2", "1-feature", "../dep2"),
                ("dep3", None, None),
                ("dep5", "final2", None),
            ],
        ),
    )
    Git(workspace_path / "dep2").checkout("main")
    run(["git", "remote", "set-url", "origin", path2url(repos_path / "two" / "dep1")], cwd=workspace_path / "dep1")
    Git(workspace_path / "dep4").checkout("4-feature")

    for _ in range(2):
        assert cli(["dep", "update", "revision"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "main", "../dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", "main", "../dep1"),
                    ("dep2", "main", "../dep2"),
                    ("dep3", "main", None),
                    ("dep5", "final2", None),
                ],
            ),
        )

    for _ in range(2):
        assert cli(["dep", "update", "revision", "--recursive"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "4-feature", "../dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", "main", "../dep1"),
                    ("dep2", "main", "../dep2"),
                    ("dep3", "main", None),
                    ("dep5", "final2", None),
                ],
            ),
        )


def test_cli_dep_update_url(tmp_path, workspace_path):
    """Test Update URL."""
    repos_path = workspace_path.parent / "repos"
    assert tuple(_get_infos(workspace_path)) == (
        ("dep1", [("dep4", "main", "../dep4")]),
        ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
        ("dep3", [("dep2", None, "../dep2")]),
        (
            "main",
            [
                ("dep1", None, "../dep1"),
                ("dep2", "1-feature", "../dep2"),
                ("dep3", None, None),
                ("dep5", "final2", None),
            ],
        ),
    )
    Git(workspace_path / "dep2").checkout("main")
    run(["git", "remote", "set-url", "origin", path2url(repos_path / "two" / "dep1")], cwd=workspace_path / "dep1")
    Git(workspace_path / "dep4").checkout("4-feature")

    for _ in range(2):
        assert cli(["dep", "update", "url"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "main", "../dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", None, "../../two/dep1"),
                    ("dep2", "1-feature", None),
                    ("dep3", None, None),
                    ("dep5", "final2", None),
                ],
            ),
        )

    for _ in range(2):
        assert cli(["dep", "update", "url", "--recursive"], tmp_path=tmp_path) == [""]
        assert tuple(_get_infos(workspace_path)) == (
            ("dep1", [("dep4", "main", "../../one/dep4")]),
            ("dep2", [("dep3", None, None), ("dep4", "main", "../dep4")]),
            ("dep3", [("dep2", None, "../dep2")]),
            (
                "main",
                [
                    ("dep1", None, "../../two/dep1"),
                    ("dep2", "1-feature", None),
                    ("dep3", None, None),
                    ("dep5", "final2", None),
                ],
            ),
        )


def test_cli_dep_update_revision_default(tmp_path):
    """Update Revision to Default."""
    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "main.git", commit="initial") as path:
        (path / "data.txt").write_text("main")
        ManifestSpec(
            defaults={"revision": "main"},
            dependencies=[
                ProjectSpec(name="dep1", revision="main"),
            ],
        ).save(path / "git-ws.toml")
    with git_repo(repos_path / "dep1.git", commit="initial") as path:
        (path / "data.txt").write_text("dep")

    # Clone
    with chdir(tmp_path):
        assert cli(["clone", path2url(repos_path / "main"), "--update"], tmp_path=tmp_path, repos_path=repos_path,) == [
            "===== main/main (MAIN 'main') =====",
            "Cloning 'file://REPOS/main'.",
            "===== main/dep1 ('dep1', revision='main') =====",
            "Cloning 'file://REPOS/dep1'.",
            "",
        ]
        workspace_path = tmp_path / "main"

    with chdir(workspace_path):
        assert tuple(_get_infos(workspace_path)) == (("main", [("dep1", "main", None)]),)

        assert cli(["dep", "update", "revision"], tmp_path=tmp_path) == [""]

        assert tuple(_get_infos(workspace_path)) == (("main", [("dep1", None, None)]),)
