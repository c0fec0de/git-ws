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
from pytest import fixture

from gitws import GitWS
from gitws.datamodel import ManifestSpec, ProjectSpec

from .common import TESTDATA_PATH

# pylint: disable=unused-import
from .fixtures import git_repo
from .util import assert_gen, chdir, check, format_logs


@fixture
def repos_deptop(tmp_path):
    """Fixture dep back to top."""

    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "top", commit="initial") as path:
        (path / "data.txt").write_text("top")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep2", url="../dep2"),
            ],
        ).save(path / "git-ws.toml")

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3", revision="main"),
                ProjectSpec(name="top", url="../top"),
            ]
        ).save(path / "git-ws.toml")

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3", revision="main"),
            ],
        ).save(path / "git-ws.toml")

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="top"),
            ],
        ).save(path / "git-ws.toml")

    yield repos_path


def test_deptop(tmp_path, repos_deptop, caplog):
    """Initialized :any:`GitWS` on `repos_deptop`."""
    workspace = tmp_path / "top"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_deptop / "top"))

        check(workspace, "top")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)

        gws.update(skip_main=True)

        check(workspace, "top")
        check(workspace, "dep1")
        check(workspace, "dep2")
        check(workspace, "dep3")

    assert_gen(tmp_path / "gen", TESTDATA_PATH / "cli_cornercases" / "deptop", caplog=caplog, tmp_path=tmp_path)
