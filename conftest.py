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

"""Pytest Configuration and Fixtures."""

import tempfile
from pathlib import Path

import pytest

# https://stackoverflow.com/questions/46962007/how-to-automatically-change-to-pytest-temporary-directory-for-all-doctests
from gitws import ManifestSpec, ProjectSpec, save
from tests.fixtures import create_repos, git_repo


@pytest.fixture(autouse=True)
def _docdir(request):
    # Trigger ONLY for the doctests.
    doctest_plugin = request.config.pluginmanager.getplugin("doctest")
    if isinstance(request.node, doctest_plugin.DoctestItem):
        # Get the fixture dynamically by its name.
        tmpdir = request.getfixturevalue("tmpdir")

        # Chdir only for the duration of the test.
        with tmpdir.as_cwd():
            yield

    else:
        # For normal tests, we have to yield, since this is a yield-fixture.
        yield


@pytest.fixture(scope="session")
def repos():
    """Fixture with main and four dependency repos."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        create_repos(repos_path)

        yield repos_path


@pytest.fixture(scope="session")
def repos_dotgit():
    """Fixture with main and four dependency repos."""
    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:
        repos_path = Path(tmpdir)

        # with .git
        with git_repo(repos_path / "main.git", commit="initial") as path:
            (path / "data.txt").write_text("main")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep1", revision="main"),
                    ProjectSpec(name="dep3", url="../dep3", revision="main"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        # with .git
        with git_repo(repos_path / "dep1.git", commit="initial") as path:
            (path / "data.txt").write_text("dep1")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep2", revision="main"),
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        # with .git
        with git_repo(repos_path / "dep2.git", commit="initial") as path:
            (path / "data.txt").write_text("dep2")

        # non .git
        with git_repo(repos_path / "dep3", commit="initial") as path:
            (path / "data.txt").write_text("dep3")
            manifest_spec = ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep4", revision="main"),  # refer to non .git
                ],
            )
            save(manifest_spec, path / "git-ws.toml")

        # non .git
        with git_repo(repos_path / "dep4", commit="initial") as path:
            (path / "data.txt").write_text("dep4")

        yield repos_path
