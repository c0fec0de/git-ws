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

"""Fixtures."""
from contextlib import contextmanager
from pathlib import Path

from gitws import Defaults, Git, ManifestSpec, ProjectSpec, save

from .util import chdir, run


def set_meta(path=None):
    """Set Meta Data for Commits."""
    run(("git", "config", "user.email", "you@example.com"), check=True, cwd=path)
    run(("git", "config", "user.name", "you"), check=True, cwd=path)


@contextmanager
def git_repo(path, commit=None, branch="main", origin=None):
    """Initialize Repo."""
    path.mkdir(parents=True, exist_ok=True)
    with chdir(path):
        run(("git", "init"), check=True)
        run(("git", "checkout", "-b", branch), check=True)
        set_meta()
        yield path
        run(("git", "add", "-A"), check=True)
        run(("git", "commit", "-m", commit), check=True)
        if origin:
            run(("git", "remote", "add", "origin", origin))


def create_repos(repos_path, add_dep5=False, add_dep6=False):  # noqa: PLR0915
    """Create Test Repos."""
    with git_repo(repos_path / "dep6", commit="initial") as path:
        (path / "data.txt").write_text("dep6")

    dep6_sha = Git(repos_path / "dep6").get_sha()

    with chdir(repos_path / "dep6"):
        Path("other.txt").touch()
        run(("git", "add", "other.txt"), check=True)
        run(("git", "commit", "-m", "other"), check=True)

    with git_repo(repos_path / "main", commit="initial") as path:
        (path / "data.txt").write_text("main")
        dependencies = [
            ProjectSpec(name="dep1", url="../dep1"),
            ProjectSpec(name="dep2", url="../dep2", revision="1-feature", submodules=False),
            ProjectSpec(name="dep3", groups=("test",)),
        ]
        if add_dep5:
            dependencies.append(ProjectSpec(name="dep5", revision="final2"))
        if add_dep6:
            dependencies.append(ProjectSpec(name="dep6", revision=dep6_sha))

        manifest_spec = ManifestSpec(
            group_filters=("-test",),
            dependencies=dependencies,
        )
        save(manifest_spec, path / "git-ws.toml")

    with chdir(repos_path / "main"):
        Path("other.txt").touch()
        run(("git", "add", "other.txt"), check=True)
        run(("git", "commit", "-m", "other"), check=True)

    with chdir(repos_path / "main"):
        manifest_spec = ManifestSpec(
            defaults=Defaults(revision="main"),
            group_filters=("+foo", "+bar", "-fast"),
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep6", url="../dep6", path="sub/dep6", groups=["foo", "bar", "fast"]),
                ProjectSpec(name="dep4", url="../dep4", revision="4-feature"),
            ],
        )
        save(manifest_spec, path / "other.toml")
        run(("git", "add", "other.toml"), check=True)
        run(("git", "commit", "-m", "other"), check=True)

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep4", url="../dep4", revision="main"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

    with chdir(repos_path / "dep1"):
        Path("other.txt").touch()
        run(("git", "add", "other.txt"), check=True)
        run(("git", "commit", "-m", "other"), check=True)

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        manifest_spec = ManifestSpec(
            defaults=Defaults(revision="main"),
            group_filters=("-test",),
            dependencies=[
                ProjectSpec(name="dep3", groups=("test",)),
                ProjectSpec(name="dep4", url="../dep4", revision="main"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

    with chdir(repos_path / "dep2"):
        run(("git", "checkout", "-b", "1-feature"), check=True)
        (path / "data.txt").write_text("dep2-feature")
        run(("git", "add", "data.txt"), check=True)
        run(("git", "commit", "-m", "feature"), check=True)
        run(("git", "checkout", "main"), check=True)

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")
        manifest_spec = ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep2", url="../dep2"),
            ],
        )
        save(manifest_spec, path / "git-ws.toml")

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
    run(("git", "tag", "final2"), check=True, cwd=repos_path / "dep5")
