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

"""Non-Recursive."""

from pytest import fixture

from gitws import GitWS, ManifestSpec, ProjectSpec, save

from .fixtures import git_repo
from .util import chdir, check, path2url


@fixture
def repos(tmp_path):
    """Return Example Repos."""
    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "main", commit="initial") as path:
        (path / "data.txt").write_text("main")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep1"),
                ProjectSpec(name="dep2", recursive=False),
                ProjectSpec(name="dep3"),
            ]
        )
        save(manifest_spec, path / "git-ws.toml")

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep4", revision="main"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep5", revision="main"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep6", revision="main"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

    with git_repo(repos_path / "dep4", commit="initial") as path:
        (path / "data.txt").write_text("dep4")

    with git_repo(repos_path / "dep5", commit="initial") as path:
        (path / "data.txt").write_text("dep5")

    with git_repo(repos_path / "dep6", commit="initial") as path:
        (path / "data.txt").write_text("dep6")

    yield repos_path


def test_non_recursive(repos, tmp_path):
    """Non Recursive."""
    with chdir(tmp_path):
        gitws = GitWS.clone(path2url(repos / "main"))
        gitws.update()
        workspace = gitws.path
        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)
        check(workspace, "dep6")

    assert [manifest.path for manifest in gitws.manifests()] == [
        str(workspace / "main" / "git-ws.toml"),
        str(workspace / "dep1" / "git-ws.toml"),
        str(workspace / "dep3" / "git-ws.toml"),
    ]

    assert [project.path for project in gitws.projects()] == [
        "main",
        "dep1",
        "dep2",
        "dep3",
        "dep4",
        "dep6",
    ]
