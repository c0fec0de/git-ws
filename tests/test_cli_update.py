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

"""Command Line Interface - Update Variants."""
from pytest import fixture

from gitws import GitWS
from gitws.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_output, run


@fixture
def gws(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        gws = GitWS.clone(str(repos / "main"))
        gws.update(skip_main=True)

        yield gws


def test_update(tmp_path, repos, gws):
    """Test update."""
    # pylint: disable=unused-argument

    # Modify dep4
    path = repos / "dep4"
    ManifestSpec(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "git-ws.toml")
    run(("git", "add", "git-ws.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Update project
    assert cli(["update", "-P", "dep2"]) == [
        "===== SKIPPING main (MAIN) =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== SKIPPING dep4 (revision='main') =====",
        "",
    ]

    # Update
    assert cli(["update"], tmp_path=tmp_path) == [
        "===== main (MAIN) =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]

    # Update again
    assert cli(["update"]) == [
        "===== main (MAIN) =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Pulling branch 'main'.",
        "",
    ]

    # Update other.toml
    assert cli(["update", "--manifest", "other.toml"], tmp_path=tmp_path) == [
        "===== main (MAIN) =====",
        "Pulling branch 'main'.",
        "===== dep1 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Merging branch '4-feature'.",
        "",
    ]


def test_update_rebase(tmp_path, repos, gws):
    """Test update --rebase."""
    # pylint: disable=unused-argument

    # Modify dep4
    path = repos / "dep4"
    ManifestSpec(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "git-ws.toml")
    run(("git", "add", "git-ws.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Rebase
    assert cli(["update", "--rebase"], tmp_path=tmp_path) == [
        "===== main (MAIN) =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]

    assert cli(["update", "--rebase"]) == [
        "===== main (MAIN) =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "",
    ]

    assert cli(["update", "--manifest", "other.toml", "--rebase"], tmp_path=tmp_path) == [
        "===== main (MAIN) =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Rebasing branch '4-feature'.",
        "",
    ]

    assert cli(["status"]) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "git-ws WARNING Clone dep4 (revision='main') is on different revision: '4-feature'",
        "",
    ]
