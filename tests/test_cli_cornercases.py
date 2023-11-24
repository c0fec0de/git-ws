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
import tempfile
from pathlib import Path

from pytest import fixture

from gitws import GitWS, ManifestSpec, ProjectSpec, save

from .common import TESTDATA_PATH
from .fixtures import git_repo
from .util import assert_gen, chdir, check


@fixture
def repos_deptop():
    """Fixture dep back to top."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        with git_repo(repos_path / "top", commit="initial") as path:
            (path / "data.txt").write_text("top")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep1", url="../dep1"),
                    ProjectSpec(name="dep2", url="../dep2"),
                    ProjectSpec(name="sub/dep4"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "dep1", commit="initial") as path:
            (path / "data.txt").write_text("dep1")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep3", url="../dep3", revision="main"),
                    ProjectSpec(name="top", url="../top"),
                ]
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "dep2", commit="initial") as path:
            (path / "data.txt").write_text("dep2")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep3", url="../dep3", revision="main"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "dep3", commit="initial") as path:
            (path / "data.txt").write_text("dep3")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="top"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "sub" / "dep4", commit="initial") as path:
            (path / "data.txt").write_text("dep4")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep5"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        with git_repo(repos_path / "sub" / "dep5", commit="initial") as path:
            (path / "data.txt").write_text("dep5")

        yield repos_path


def test_deptop(tmp_path, repos_deptop, caplog, capsys):
    """Initialized :any:`GitWS` on ``repos_deptop``."""
    workspace = tmp_path / "top"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_deptop / "top"))

        check(workspace, "top")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)
        check(workspace, "dep4", path="sub/dep4", exists=False)
        check(workspace, "dep5", path="sub/dep5", exists=False)

        gws.update(skip_main=True)

        check(workspace, "top")
        check(workspace, "dep1")
        check(workspace, "dep2")
        check(workspace, "dep3")
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5")
        check(workspace, "dep4", path="sub/dep4")
        check(workspace, "dep5", path="sub/dep5", exists=False)

    assert_gen(
        tmp_path / "gen",
        TESTDATA_PATH / "cli_cornercases" / "deptop",
        caplog=caplog,
        capsys=capsys,
        tmp_path=tmp_path,
        repos_path=repos_deptop,
    )
