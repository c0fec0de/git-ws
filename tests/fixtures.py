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

"""Fixtures."""
from contextlib import contextmanager

from pytest import fixture

from gitws.datamodel import Defaults, ManifestSpec, ProjectSpec

from .util import chdir, run


@contextmanager
def git_repo(path, commit=None):
    """Initialize Repo."""
    path.mkdir(parents=True, exist_ok=True)
    with chdir(path):
        run(("git", "init"), check=True)
        run(("git", "checkout", "-b", "main"), check=True)
        run(("git", "config", "user.email", "you@example.com"), check=True)
        run(("git", "config", "user.name", "you"), check=True)
        yield path
        run(("git", "add", "-A"), check=True)
        run(("git", "commit", "-m", commit), check=True)


@fixture
def repos(tmp_path):
    """Fixture with main and four depedency repos."""

    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "main", commit="initial") as path:
        (path / "data.txt").write_text("main")
        ManifestSpec(
            group_filters=("-test",),
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep2", url="../dep2", revision="1-feature"),
                ProjectSpec(name="dep3", url="../dep3", groups=("test",)),
            ],
        ).save(path / "git-ws.toml")

    with chdir(repos_path / "main"):
        ManifestSpec(
            defaults=Defaults(revision="main"),
            group_filters=("+foo", "+bar", "-fast"),
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep6", url="../dep6", path="sub/dep6", groups=["foo", "bar", "fast"]),
                ProjectSpec(name="dep4", url="../dep4", revision="4-feature"),
            ],
        ).save(path / "other.toml")
        run(("git", "add", "other.toml"), check=True)
        run(("git", "commit", "-m", "other"), check=True)

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep4", url="../dep4", revision="main"),
            ],
        ).save(path / "git-ws.toml")

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        ManifestSpec(
            defaults=Defaults(revision="main"),
            group_filters=("-test",),
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3", groups=("test",)),
                ProjectSpec(name="dep4", url="../dep4", revision="main"),
            ],
        ).save(path / "git-ws.toml")

    with chdir(repos_path / "dep2"):
        run(("git", "checkout", "-b", "1-feature"), check=True)
        (path / "data.txt").write_text("dep2-feature")
        run(("git", "add", "data.txt"), check=True)
        run(("git", "commit", "-m", "feature"), check=True)
        run(("git", "checkout", "main"), check=True)

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep2", url="../dep2"),
            ],
        ).save(path / "git-ws.toml")

    run(("git", "tag", "v1.0"), check=True, cwd=repos_path / "dep3")

    with git_repo(repos_path / "dep4", commit="initial") as path:
        (path / "data.txt").write_text("dep4")

    with chdir(repos_path / "dep4"):
        run(("git", "checkout", "-b", "4-feature"), check=True)
        (path / "data.txt").write_text("dep4-feature")
        run(("git", "add", "data.txt"), check=True)
        run(("git", "commit", "-m", "feature"), check=True)
        run(("git", "checkout", "main"), check=True)

    with git_repo(repos_path / "dep5", commit="initial") as path:
        (path / "data.txt").write_text("dep5")

    with git_repo(repos_path / "dep6", commit="initial") as path:
        (path / "data.txt").write_text("dep6")

    yield repos_path
