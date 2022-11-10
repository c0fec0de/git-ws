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
import tempfile
from pathlib import Path

from pytest import fixture

from gitws import GitWS
from gitws.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import
from .fixtures import git_repo
from .util import chdir, check, cli, format_output, run


@fixture(scope="session")
def repos_submodules():
    """Fixture with main and four depedency repos."""

    with tempfile.TemporaryDirectory(prefix="git-ws-test-repos") as tmpdir:

        repos_path = Path(tmpdir)

        with git_repo(repos_path / "main", commit="initial") as path:
            (path / "data.txt").write_text("main")
            ManifestSpec(
                group_filters=("-test",),
                dependencies=[
                    ProjectSpec(name="dep1"),
                ],
            ).save(path / "git-ws.toml")

        with git_repo(repos_path / "sm1", commit="initial") as path:
            (path / "data.txt").write_text("sm1")

        with git_repo(repos_path / "sm2", commit="initial") as path:
            (path / "data.txt").write_text("sm2")

        with git_repo(repos_path / "dep1", commit="initial") as path:
            (path / "data.txt").write_text("dep1")
            ManifestSpec(
                dependencies=[
                    ProjectSpec(name="dep2", revision="main"),
                ],
            ).save(path / "git-ws.toml")

        # run(["git", "submodule", "add", "../sm1", "sm1"], cwd=(repos_path / "dep1"), check=True)
        # run(["git", "commit", "-am", "add-submodule"], cwd=(repos_path / "dep1"), check=True)

        with git_repo(repos_path / "dep2", commit="initial") as path:
            (path / "data.txt").write_text("dep2")

        # run(["git", "submodule", "add", "../sm2", "sm2"], cwd=(repos_path / "dep2"), check=True)
        # run(["git", "commit", "-am", "add-submodule"], cwd=(repos_path / "dep2"), check=True)

        yield repos_path


@fixture
def gws(tmp_path, repos_submodules):
    """Initialized :any:`GitWS` on `repos_submodules`."""
    with chdir(tmp_path):
        gws = GitWS.clone(str(repos_submodules / "main"))
        gws.update(skip_main=True)

    with chdir(gws.main_path):
        yield gws


def test_update(tmp_path, repos_submodules, gws):
    """Test update."""
    # pylint: disable=unused-argument
    assert cli(["-vv", "submodule", "update"], tmp_path=tmp_path, repos_path=repos_submodules) == [
        "git-ws INFO Workspace path=TMP/main main=main",
        "git-ws INFO AppConfigData(manifest_path='git-ws.toml', color_ui=True, group_filters=None)",
        "git-ws DEBUG run(['git', 'describe', '--exact-match', '--tags'], cwd='.') OK "
        "stdout=b'' stderr=b'fatal: No names found, cannot describe anything.\\n'",
        "git-ws INFO Git('.').get_tag() = None",
        "git-ws DEBUG run(['git', 'branch'], cwd='.') OK stdout=b'* main\\n' stderr=b''",
        "git-ws INFO Git('.').get_branch() = 'main'",
        "===== . (MAIN 'main', revision='main') =====",
        "git-ws DEBUG run(['git', 'rev-parse', '--show-cdup'], cwd='.') OK stdout=b'\\n' stderr=b''",
        "git-ws INFO Git('.').is_cloned() = True",
        "git-ws DEBUG run(['git', 'describe', '--exact-match', '--tags'], cwd='.') OK "
        "stdout=b'' stderr=b'fatal: No names found, cannot describe anything.\\n'",
        "git-ws INFO Git('.').get_tag() = None",
        "git-ws DEBUG run(['git', 'branch'], cwd='.') OK stdout=b'* main\\n' stderr=b''",
        "git-ws INFO Git('.').get_branch() = 'main'",
        "git-ws DEBUG run(('git', 'submodule', 'update'), cwd='.') OK stdout=None stderr=None",
        "git-ws DEBUG run(['git', 'remote', '-v'], cwd='.') OK "
        "stdout=b'origin\\tREPOS/main "
        "(fetch)\\norigin\\tREPOS/main "
        "(push)\\n' stderr=b''",
        "git-ws INFO Git('.').get_url() = 'REPOS/main'",
        "git-ws DEBUG ManifestSpec(group_filters=('-test',), dependencies=(ProjectSpec(name='dep1'),))",
        "git-ws DEBUG Project(name='dep1', path='dep1', url='../dep1')",
        "===== ../dep1 ('dep1') =====",
        "git-ws DEBUG run(['git', 'rev-parse', '--show-cdup'], cwd='../dep1') OK stdout=b'\\n' stderr=b''",
        "git-ws INFO Git('../dep1').is_cloned() = True",
        "git-ws WARNING Clone dep1 has no revision!",
        "git-ws DEBUG run(('git', 'submodule', 'update'), cwd='../dep1') OK stdout=None stderr=None",
        "git-ws DEBUG run(['git', 'remote', '-v'], cwd='../dep1') OK "
        "stdout=b'origin\\tREPOS/dep1 "
        "(fetch)\\norigin\\tREPOS/dep1 "
        "(push)\\n' stderr=b''",
        "git-ws INFO Git('../dep1').get_url() = 'REPOS/dep1'",
        "git-ws DEBUG ManifestSpec(dependencies=(ProjectSpec(name='dep2', revision='main'),))",
        "git-ws DEBUG Project(name='dep2', path='dep2', url='../dep2', revision='main')",
        "===== ../dep2 ('dep2', revision='main') =====",
        "git-ws DEBUG run(['git', 'rev-parse', '--show-cdup'], cwd='../dep2') OK stdout=b'\\n' stderr=b''",
        "git-ws INFO Git('../dep2').is_cloned() = True",
        "git-ws DEBUG run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='../dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "git-ws INFO Git('../dep2').get_tag() = None",
        "git-ws DEBUG run(['git', 'branch'], cwd='../dep2') OK stdout=b'* main\\n' stderr=b''",
        "git-ws INFO Git('../dep2').get_branch() = 'main'",
        "git-ws DEBUG run(('git', 'submodule', 'update'), cwd='../dep2') OK stdout=None stderr=None",
        "",
    ]

    workspace = gws.path
    check(workspace, "dep1")
    check(workspace, "dep2")
    # check(workspace, "sm1", path="dep1/sm1")
    # check(workspace, "sm2", path="dep2/sm2")
