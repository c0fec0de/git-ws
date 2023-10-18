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

from gitws import Git, GitWS
from gitws.datamodel import FileRef, MainFileRef, ManifestSpec, ProjectSpec

from .fixtures import git_repo

# pylint: disable=unused-import
from .util import chdir, cli, format_output, run


def create_repos(repos_path) -> str:
    """Create Test Repos."""
    with git_repo(repos_path / "main", commit="initial") as path:
        (path / "data0.txt").write_text("main-0")
        (path / "data1.txt").write_text("main-1")
        (path / "data2.txt").write_text("main-2")
        ManifestSpec(
            copyfiles=[
                MainFileRef(src="data0.txt", dest="main-data0.txt"),
                MainFileRef(src="data1.txt", dest="build/main-data1.txt"),
                MainFileRef(src="data3.txt", dest="main-data3.txt"),
            ],
            dependencies=[
                ProjectSpec(
                    name="dep1",
                    revision="main",
                    copyfiles=[
                        FileRef(src="data0.txt", dest="dep1-data0.txt"),
                        FileRef(src="data1.txt", dest="build/dep1-data1.txt"),
                        FileRef(src="data3.txt", dest="dep1-data3.txt"),
                    ],
                ),
            ],
        ).save(path / "git-ws.toml")

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data0.txt").write_text("dep1-0")
        (path / "data1.txt").write_text("dep1-1")
        (path / "data2.txt").write_text("dep1-2")
        ManifestSpec().save(path / "git-ws.toml")

    return Git(repos_path / "main").get_sha()[:7]


def modify_repos(repos_path) -> str:
    """Update."""
    with chdir(repos_path / "main"):
        ManifestSpec(
            copyfiles=[
                MainFileRef(src="data0.txt", dest="main-data0.txt"),
                MainFileRef(src="data2.txt", dest="main-data2.txt"),
            ],
            dependencies=[
                ProjectSpec(
                    name="dep1",
                    revision="main",
                    copyfiles=[
                        FileRef(src="data0.txt", dest="dep1-data0.txt"),
                        FileRef(src="data2.txt", dest="dep1-data2.txt"),
                    ],
                ),
            ],
        ).save(Path("git-ws.toml"))
        Path("data0.txt").write_text("main-0 - update", encoding="utf-8")
        git = Git(Path("."))
        git.commit("update", all_=True)
        return git.get_sha()[:7]


def test_update(tmp_path):
    """Test Update."""
    # pylint: disable=unused-argument

    repos_path = tmp_path / "repos"
    sha_initial = create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_path / "main"))

    with chdir(gws.path):

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Cloning 'REPOS/dep1'.",
            "===== Update Referenced Files =====",
            "Copying 'main/data0.txt' -> 'main-data0.txt'",
            "Copying 'main/data1.txt' -> 'build/main-data1.txt'",
            "ERROR:   Cannot update: source file 'main/data3.txt' does not exists!",
            "Copying 'dep1/data0.txt' -> 'dep1-data0.txt'",
            "Copying 'dep1/data1.txt' -> 'build/dep1-data1.txt'",
            "ERROR:   Cannot update: source file 'dep1/data3.txt' does not exists!",
            "Aborted!",
            "",
        ]

        assert Path("main-data0.txt").read_text(encoding="utf-8") == "main-0"
        assert Path("build/main-data1.txt").read_text(encoding="utf-8") == "main-1"
        assert not Path("main-data2.txt").exists()
        assert Path("dep1-data0.txt").read_text(encoding="utf-8") == "dep1-0"
        assert Path("build/dep1-data1.txt").read_text(encoding="utf-8") == "dep1-1"
        assert not Path("dep1-data2.txt").exists()

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== Update Referenced Files =====",
            "ERROR:   Cannot update: source file 'main/data3.txt' does not exists!",
            "ERROR:   Cannot update: source file 'dep1/data3.txt' does not exists!",
            "Aborted!",
            "",
        ]

        sha_update = modify_repos(repos_path)

        assert not Path("build/main-data1.txt").unlink()

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "From REPOS/main",
            f"   {sha_initial}..{sha_update}  main       -> origin/main",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== Update Referenced Files =====",
            "Removing 'build/dep1-data1.txt'",
            "Removing 'main-data0.txt'",
            "Copying 'main/data0.txt' -> 'main-data0.txt'",
            "Copying 'main/data2.txt' -> 'main-data2.txt'",
            "Copying 'dep1/data2.txt' -> 'dep1-data2.txt'",
            "",
        ]

        assert Path("main-data0.txt").read_text(encoding="utf-8") == "main-0 - update"
        assert not Path("build/main-data1.txt").exists()
        assert Path("main-data2.txt").read_text(encoding="utf-8") == "main-2"
        assert Path("dep1-data0.txt").read_text(encoding="utf-8") == "dep1-0"
        assert not Path("build/dep1-data1.txt").exists()
        assert Path("dep1-data2.txt").read_text(encoding="utf-8") == "dep1-2"

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== Update Referenced Files =====",
            "",
        ]


def test_no_main(tmp_path):
    """Copyfile without Main-Project"""

    with chdir(tmp_path):
        (tmp_path / "data0.txt").touch()
        (tmp_path / "data2.txt").touch()
        ManifestSpec(
            copyfiles=[
                MainFileRef(src="data0.txt", dest="main-data0.txt"),
                MainFileRef(src="data2.txt", dest="main-data2.txt"),
            ],
        ).save(Path("git-ws.toml"))

        gws = GitWS.init()

        assert not (tmp_path / "main-data0.txt").exists()
        assert not (tmp_path / "main-data2.txt").exists()

        gws.update()

        assert (tmp_path / "main-data0.txt").exists()
        assert (tmp_path / "main-data2.txt").exists()


def test_group(tmp_path):
    """Groups Filtering."""

    with chdir(tmp_path):
        (tmp_path / "data0.txt").touch()
        (tmp_path / "data1.txt").touch()
        (tmp_path / "data2.txt").touch()
        ManifestSpec(
            group_filters=["-grp"],
            copyfiles=[
                MainFileRef(src="data0.txt", dest="main-data0.txt"),
                MainFileRef(src="data1.txt", dest="main-data1.txt", groups=["ab", "cd"]),
                MainFileRef(src="data2.txt", dest="main-data2.txt", groups=["grp"]),
            ],
        ).save(Path("git-ws.toml"))

        gws = GitWS.init()

        assert not (tmp_path / "main-data0.txt").exists()
        assert not (tmp_path / "main-data1.txt").exists()
        assert not (tmp_path / "main-data2.txt").exists()

        gws.update()

        assert (tmp_path / "main-data0.txt").exists()
        assert (tmp_path / "main-data1.txt").exists()
        assert not (tmp_path / "main-data2.txt").exists()


def test_existing(tmp_path):
    """Test Existing."""
    # pylint: disable=unused-argument

    repos_path = tmp_path / "repos"
    create_repos(repos_path)

    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_path / "main"))

    with chdir(gws.path):

        Path("build").mkdir()
        Path("build/main-data1.txt").touch()

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Cloning 'REPOS/dep1'.",
            "===== Update Referenced Files =====",
            "Copying 'main/data0.txt' -> 'main-data0.txt'",
            "ERROR:   Cannot update: destination file 'build/main-data1.txt' already exists!",
            "ERROR:   Cannot update: source file 'main/data3.txt' does not exists!",
            "Copying 'dep1/data0.txt' -> 'dep1-data0.txt'",
            "Copying 'dep1/data1.txt' -> 'build/dep1-data1.txt'",
            "ERROR:   Cannot update: source file 'dep1/data3.txt' does not exists!",
            "Aborted!",
            "",
        ]

        assert Path("main-data0.txt").read_text(encoding="utf-8") == "main-0"
        assert Path("build/main-data1.txt").read_text(encoding="utf-8") == ""
        assert not Path("main-data2.txt").exists()
        assert Path("dep1-data0.txt").read_text(encoding="utf-8") == "dep1-0"
        assert Path("build/dep1-data1.txt").read_text(encoding="utf-8") == "dep1-1"
        assert not Path("dep1-data2.txt").exists()

        assert cli(["update"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== Update Referenced Files =====",
            "ERROR:   Cannot update: destination file 'build/main-data1.txt' already exists!",
            "ERROR:   Cannot update: source file 'main/data3.txt' does not exists!",
            "ERROR:   Cannot update: source file 'dep1/data3.txt' does not exists!",
            "Aborted!",
            "",
        ]
        assert cli(["update", "--force"], tmp_path=tmp_path, repos_path=repos_path, exit_code=1) == [
            "===== main (MAIN 'main', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== dep1 ('dep1', revision='main') =====",
            "Fetching.",
            "Merging branch 'main'.",
            "===== Update Referenced Files =====",
            "Copying 'main/data1.txt' -> 'build/main-data1.txt'",
            "ERROR:   Cannot update: source file 'main/data3.txt' does not exists!",
            "ERROR:   Cannot update: source file 'dep1/data3.txt' does not exists!",
            "Aborted!",
            "",
        ]
