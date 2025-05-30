# Copyright 2022-2025 c0fec0de
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

"""Command Line Interface - Update Variants."""

import tempfile
from pathlib import Path

from contextlib_chdir import chdir
from pytest import fixture
from test2ref import assert_refdata

from gitws import GitWS, ManifestSpec, ProjectSpec, save

from .fixtures import git_repo
from .util import check, cli, path2url


@fixture(scope="session")
def repos_submodules():
    """Fixture with main and four dependency repos."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        with git_repo(repos_path / "main", commit="initial") as path:
            (path / "data.txt").write_text("main")
            manifest_spec = ManifestSpec(
                group_filters=("-test",),
                dependencies=[
                    ProjectSpec(name="dep1"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "sm1", commit="initial") as path:
            (path / "data.txt").write_text("sm1")

        with git_repo(repos_path / "sm2", commit="initial") as path:
            (path / "data.txt").write_text("sm2")

        with git_repo(repos_path / "dep1", commit="initial") as path:
            (path / "data.txt").write_text("dep1")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep2", revision="main"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        # run(["git", "submodule", "add", "../sm1", "sm1"], cwd=(repos_path / "dep1"), check=True)
        # run(["git", "commit", "-am", "add-submodule"], cwd=(repos_path / "dep1"), check=True)

        with git_repo(repos_path / "dep2", commit="initial") as path:
            (path / "data.txt").write_text("dep2")

        # run(["git", "submodule", "add", "../sm2", "sm2"], cwd=(repos_path / "dep2"), check=True)
        # run(["git", "commit", "-am", "add-submodule"], cwd=(repos_path / "dep2"), check=True)

        yield repos_path


@fixture
def gws(tmp_path, repos_submodules):
    """Initialize :any:`GitWS` on ``repos_submodules``."""
    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_submodules / "main"))
        gws.update(skip_main=True)

    with chdir(gws.main_path):
        yield gws


def test_update(tmp_path, repos_submodules, gws):
    """Test update."""
    gen_path = tmp_path / "gen"
    gen_path.mkdir()

    out = cli(["-vv", "submodule", "update"], tmp_path=tmp_path, repos_path=repos_submodules)
    (gen_path / "out.txt").write_text("\n".join(out))

    replacements = ((repos_submodules, "REPOS_PATH"),)
    assert_refdata(test_update, gen_path, replacements=replacements)

    workspace = gws.path
    check(workspace, "dep1")
    check(workspace, "dep2")
    # check(workspace, "sm1", path="dep1/sm1")
    # check(workspace, "sm2", path="dep2/sm2")
