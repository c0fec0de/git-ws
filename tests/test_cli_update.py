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
from pathlib import Path

from pytest import fixture

from gitws import Git, GitWS
from gitws.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_output, run


@fixture
def gws(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "main"

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos / "main"))
        gws.update(skip_main=True)

    with chdir(workspace):
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
    git4 = Git(path)
    sha1 = git4.get_sha()[:7]
    git4.add(paths=(Path("git-ws.toml"),))
    git4.commit("adapt dep")
    sha2 = git4.get_sha()[:7]

    # Update project
    assert cli(["update", "-P", "dep2"]) == [
        "===== SKIPPING main (MAIN 'main', revision='main') =====",
        "===== SKIPPING dep1 ('dep1') =====",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== SKIPPING dep4 ('dep4', revision='main') =====",
        "",
    ]

    # Update
    assert cli(["update"], tmp_path=tmp_path, repos_path=repos) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Pulling branch 'main'.",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 ('dep4', revision='main') =====",
        "Pulling branch 'main'.",
        "From REPOS/dep4",
        f"   {sha1}..{sha2}  main       -> origin/main",
        "===== dep5 ('dep5') =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Cloning 'REPOS/dep5'.",
        "",
    ]

    # Update again
    assert cli(["update"]) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep1 ('dep1') =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "Pulling branch 'main'.",
        "===== dep2 ('dep2', revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 ('dep4', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 ('dep5') =====",
        "git-ws WARNING Clone dep5 has no revision!",
        "Pulling branch 'main'.",
        "",
    ]

    # Modify dep5 to prevent deletion
    (gws.path / "dep5" / "file.txt").touch()

    # Update other.toml - FAILING
    assert cli(["update", "--manifest", "other.toml", "--prune"], tmp_path=tmp_path, repos_path=repos, exit_code=1) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep1 ('dep1', revision='main') =====",
        "Pulling branch 'main'.",
        "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
        "Cloning 'REPOS/dep6'.",
        "===== dep4 ('dep4', revision='4-feature') =====",
        "Fetching.",
        "Switched to a new branch '4-feature'",
        "Merging branch '4-feature'.",
        "===== dep5 (OBSOLETE) =====",
        "Removing 'dep5'.",
        "Error: Git Clone 'dep5' contains changes.",
        "",
        "Commit/Push all your changes and branches or use '--force'",
        "",
        "",
    ]

    assert cli(["update", "--manifest", "other.toml", "--prune", "--force"], tmp_path=tmp_path) == [
        "===== main (MAIN 'main', revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep1 ('dep1', revision='main') =====",
        "Pulling branch 'main'.",
        "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
        "Pulling branch 'main'.",
        "===== dep4 ('dep4', revision='4-feature') =====",
        "Pulling branch '4-feature'.",
        "===== dep5 (OBSOLETE) =====",
        "Removing 'dep5'.",
        "===== dep2 (OBSOLETE) =====",
        "Removing 'dep2'.",
        "",
    ]


# def test_update_rebase(tmp_path, repos, gws):
#     """Test update --rebase."""
#     # pylint: disable=unused-argument

#     # Modify dep4
#     path = repos / "dep4"
#     ManifestSpec(
#         dependencies=[
#             ProjectSpec(name="dep5", url="../dep5"),
#         ]
#     ).save(path / "git-ws.toml")
#     git4 = Git(path)
#     sha1 = git4.get_sha()[:7]
#     git4.add(paths=(Path("git-ws.toml"),))
#     git4.commit("adapt dep")
#     sha2 = git4.get_sha()[:7]

#     # Rebase
#     assert cli(["update", "--rebase"], tmp_path=tmp_path, repos_path=repos) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep1 ('dep1') =====",
#         "git-ws WARNING Clone dep1 has no revision!",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep2 ('dep2', revision='1-feature') =====",
#         "Fetching.",
#         "Rebasing branch '1-feature'.",
#         "===== dep4 ('dep4', revision='main') =====",
#         "Fetching.",
#         "From REPOS/dep4",
#         f"   {sha1}..{sha2}  main       -> origin/main",
#         "Rebasing branch 'main'.",
#         "\r"
#         "                                                                                \r"
#         "Successfully rebased and updated refs/heads/main.",
#         "===== dep5 ('dep5') =====",
#         "git-ws WARNING Clone dep5 has no revision!",
#         "Cloning 'REPOS/dep5'.",
#         "",
#     ]

#     assert cli(["update", "--rebase"]) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep1 ('dep1') =====",
#         "git-ws WARNING Clone dep1 has no revision!",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep2 ('dep2', revision='1-feature') =====",
#         "Fetching.",
#         "Rebasing branch '1-feature'.",
#         "===== dep4 ('dep4', revision='main') =====",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep5 ('dep5') =====",
#         "git-ws WARNING Clone dep5 has no revision!",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "",
#     ]

#     assert cli(["update", "--manifest", "other.toml", "--rebase"], tmp_path=tmp_path, repos_path=repos) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== dep1 ('dep1', revision='main') =====",
#         "Fetching.",
#         "Rebasing branch 'main'.",
#         "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
#         "Cloning 'REPOS/dep6'.",
#         "===== dep4 ('dep4', revision='4-feature') =====",
#         "Fetching.",
#         "Switched to a new branch '4-feature'",
#         "Rebasing branch '4-feature'.",
#         "",
#     ]

#     assert cli(["status"]) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "===== dep1 ('dep1') =====",
#         "git-ws WARNING Clone dep1 has no revision!",
#         "===== dep2 ('dep2', revision='1-feature') =====",
#         "===== dep4 ('dep4', revision='main') =====",
#         "git-ws WARNING Clone dep4 (revision='main') is on different revision: '4-feature'",
#         "",
#     ]


# def test_update_missing_origin(tmp_path, repos, gws):
#     """Test update."""
#     # pylint: disable=unused-argument

#     run(("git", "remote", "remove", "origin"), cwd=gws.path / "dep4", check=True)

#     # Update project
#     assert cli(["checkout"]) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "===== dep1 ('dep1') =====",
#         "git-ws WARNING Clone dep1 has no revision!",
#         "===== dep2 ('dep2', revision='1-feature') =====",
#         "Already on '1-feature'",
#         "===== dep4 ('dep4', revision='main') =====",
#         "Already on 'main'",
#         "",
#     ]

#     run(("git", "remote", "remove", "origin"), cwd=gws.path / "dep2", check=True)
#     assert cli(["checkout"], exit_code=1) == [
#         "===== main (MAIN 'main', revision='main') =====",
#         "===== dep1 ('dep1') =====",
#         "git-ws WARNING Clone dep1 has no revision!",
#         "===== dep2 ('dep2', revision='1-feature') =====",
#         "Already on '1-feature'",
#         "===== dep4 ('dep4', revision='main') =====",
#         "Already on 'main'",
#         "Error: Git Clone 'dep2' has not remote 'origin'. Try:",
#         "",
#         "    git remote add origin <URL>",
#         "",
#         "",
#     ]
