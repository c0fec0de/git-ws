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

"""Command Line Interface - Update Variants."""
from pathlib import Path

from gitws import Git, GitWS, save
from gitws.datamodel import ManifestSpec, ProjectSpec

from .fixtures import create_repos
from .util import chdir, check, cli, path2url, run


def test_update(tmp_path):
    """Test update."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_path / "main"))
        gws.update(skip_main=True)

    with chdir(gws.path):
        # Modify dep4
        path = repos_path / "dep4"
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep5", url="../dep5"),
            ]
        )
        save(manifest_spec, path / "git-ws.toml")
        git4 = Git(path)
        sha1 = git4.get_sha()[:7]
        git4.add(paths=(Path("git-ws.toml"),))
        git4.commit("adapt dep")
        sha2 = git4.get_sha()[:7]

        # Update project
        assert cli(["update", "-P", "dep2"]) == [
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Merging branch '1-feature'.",
            "",
        ]

        # Update
        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Merging branch '1-feature'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "From file://REPOS/dep4",
            f"   {sha1}..{sha2}  main       -> origin/main",
            "Merging branch 'main'.",
            "===== dep5 ('dep5') =====",
            "WARNING: Clone dep5 has no revision!",
            "Cloning 'file://REPOS/dep5'.",
            "",
        ]

        # Update again
        assert cli(["update"]) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Merging branch '1-feature'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep5 ('dep5') =====",
            "WARNING: Clone dep5 has no revision!",
            "Fetching.",
            "Merging branch 'main'.",
            "",
        ]

        # Modify dep5 to prevent deletion
        (gws.path / "dep5" / "file.txt").touch()

        # Update other.toml - FAILING
        assert cli(
            ["update", "--manifest", "other.toml", "--prune"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1
        ) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
            "Cloning 'file://REPOS/dep6'.",
            "===== dep4 ('dep4', revision='4-feature') =====",
            "Fetching.",
            "Switched to a new branch '4-feature'",
            "Merging branch '4-feature'.",
            "===== dep2 (OBSOLETE) =====",
            "Removing 'dep2'.",
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
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep4 ('dep4', revision='4-feature') =====",
            "Fetching.",
            "Merging branch '4-feature'.",
            "===== dep5 (OBSOLETE) =====",
            "Removing 'dep5'.",
            "",
        ]


def test_update_rebase(tmp_path):
    """Test update --rebase."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_path / "main"))
        gws.update(skip_main=True)

    with chdir(gws.path):
        # Modify dep4
        path = repos_path / "dep4"
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep5", url="../dep5"),
            ]
        )
        save(manifest_spec, path / "git-ws.toml")
        git4 = Git(path)
        sha1 = git4.get_sha()[:7]
        git4.add(paths=(Path("git-ws.toml"),))
        git4.commit("adapt dep")
        sha2 = git4.get_sha()[:7]

        # Rebase
        assert cli(["update", "--rebase"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Rebasing branch '1-feature'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "From file://REPOS/dep4",
            f"   {sha1}..{sha2}  main       -> origin/main",
            "Rebasing branch 'main'.",
            "Successfully rebased and updated refs/heads/main.",
            "===== dep5 ('dep5') =====",
            "WARNING: Clone dep5 has no revision!",
            "Cloning 'file://REPOS/dep5'.",
            "",
        ]

        assert cli(["update", "--rebase"]) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Fetching.",
            "Rebasing branch '1-feature'.",
            "===== dep4 ('dep4', revision='main') =====",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep5 ('dep5') =====",
            "WARNING: Clone dep5 has no revision!",
            "Fetching.",
            "Rebasing branch 'main'.",
            "",
        ]

        assert cli(["update", "--manifest", "other.toml", "--rebase"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Rebasing branch 'main'.",
            "===== sub/dep6 ('dep6', revision='main', groups='foo,bar,fast') =====",
            "Cloning 'file://REPOS/dep6'.",
            "===== dep4 ('dep4', revision='4-feature') =====",
            "Fetching.",
            "Switched to a new branch '4-feature'",
            "Rebasing branch '4-feature'.",
            "",
        ]

        assert cli(["status"]) == [
            "WARNING: Clone dep1 has no revision!",
            "WARNING: Clone dep4 (revision='main') is on different revision: '4-feature'",
            "",
        ]


def test_update_missing_origin(tmp_path):
    """Test update."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_path / "main"))
        gws.update(skip_main=True)

    with chdir(gws.path):
        run(("git", "remote", "remove", "origin"), cwd=gws.path / "dep4", check=True)

        # Update project
        assert cli(["checkout"], tmp_path=tmp_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Already on '1-feature'",
            "===== dep4 ('dep4', revision='main') =====",
            "Already on 'main'",
            "WARNING: Clone dep4 (revision='main') has no remote origin but intends to be: 'file://TMP/repos/dep4'",
            "",
        ]

        run(("git", "remote", "remove", "origin"), cwd=gws.path / "dep2", check=True)
        assert cli(["checkout"], exit_code=1, tmp_path=tmp_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Already on '1-feature'",
            "WARNING: Clone dep2 (revision='1-feature', submodules=False) has no remote "
            "origin but intends to be: 'file://TMP/repos/dep2'",
            "Error: Git Clone 'dep2' has not remote 'origin'. Try:",
            "",
            "    git remote add origin <URL>",
            "",
            "",
        ]

        run(("git", "remote", "add", "origin", path2url(repos_path / "dep4")), cwd=gws.path / "dep4", check=True)
        run(("git", "remote", "add", "origin", path2url(repos_path / "dep9")), cwd=gws.path / "dep2", check=True)
        assert cli(["checkout"], tmp_path=tmp_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "===== dep1 ('dep1') =====",
            "WARNING: Clone dep1 has no revision!",
            "===== dep2 ('dep2', revision='1-feature', submodules=False) =====",
            "Already on '1-feature'",
            "WARNING: Clone dep2 (revision='1-feature', submodules=False) "
            "remote origin is 'file://TMP/repos/dep9' but intends to be: 'file://TMP/repos/dep2'",
            "===== dep4 ('dep4', revision='main') =====",
            "Already on 'main'",
            "",
        ]


def test_update_manifest(tmp_path):
    """Test update manifest."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_path / "main"))
        gws.update()

        check(gws.path, "main")
        check(gws.path, "dep1")
        check(gws.path, "dep2", content="dep2-feature")
        check(gws.path, "dep3", exists=False)
        check(gws.path, "dep4")
        check(gws.path, "dep5", exists=False)

        # Update Manifest in Remote
        main_repo = repos_path / "main"
        manifest_spec = ManifestSpec(
            group_filters=("-test",),
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep2", url="../dep2", revision="main"),
                ProjectSpec(name="dep3", url="../dep3", groups=("test",)),
            ],
        )
        save(manifest_spec, main_repo / "git-ws.toml")
        main = Git(main_repo)
        main.add((Path("git-ws.toml"),))
        main.commit("update")

        # Update
        gws.update()

        check(gws.path, "main")
        check(gws.path, "dep1")
        check(gws.path, "dep2")
        check(gws.path, "dep3", exists=False)
        check(gws.path, "dep4")
        check(gws.path, "dep5", exists=False)


def test_update_missing_upstream(tmp_path):
    """Test Update With Missing Upstream."""
    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(path2url(repos_path / "main"))
        gws.update()

        Git(gws.path / "main").checkout(branch="90-new")
        Git(gws.path / "dep4").checkout(branch="90-new")

        gws.update()
