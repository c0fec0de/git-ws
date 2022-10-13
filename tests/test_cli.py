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
from shutil import rmtree

from pytest import fixture

from gitws import GitWS

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_logs


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = GitWS.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


def test_pull(tmp_path, arepo):
    """Test pull."""
    _test_foreach(tmp_path, arepo, "pull")


def test_push(tmp_path, arepo):
    """Test push."""
    # pylint: disable=unused-argument
    assert cli(("push",)) == [
        "===== dep4 (revision='main') =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== main (MAIN) =====",
        "",
    ]


def test_fetch(tmp_path, arepo):
    """Test fetch."""
    _test_foreach(tmp_path, arepo, "fetch")


def test_rebase(tmp_path, arepo):
    """Test rebase."""
    _test_foreach(tmp_path, arepo, "rebase")


def test_diff(tmp_path, arepo):
    """Test diff."""
    _test_foreach(tmp_path, arepo, "diff")


def test_deinit(tmp_path, arepo):
    """Test deinit."""
    # pylint: disable=unused-argument
    assert cli(["deinit"]) == ["Workspace deinitialized at '.'.", ""]

    assert not (tmp_path / "workspace/.gitws").exists()
    assert (tmp_path / "workspace/main").exists()

    assert cli(["deinit"], exit_code=1) == [
        "Error: git workspace has not been initialized yet. Try:",
        "",
        "    git ws init",
        "",
        "or:",
        "",
        "    git ws clone",
        "",
        "",
    ]


def test_git(tmp_path, arepo):
    """Test git."""
    # pylint: disable=unused-argument
    assert cli(["git", "status"]) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(["git", "status", "-P", "dep2", "-P", "./dep4"]) == [
        "===== SKIPPING main (MAIN) =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_foreach(tmp_path, arepo, caplog):
    """Test foreach."""
    # pylint: disable=unused-argument
    assert cli(["foreach", "git", "status"]) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert format_logs(caplog, tmp_path) == [
        "INFO    git-ws Workspace path=TMP/workspace main=main "
        "AppConfigData(manifest_path='git-ws.toml', color_ui=True, groups=None)",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='main') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('main').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='main') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(dependencies=(ProjectSpec(name='dep1', "
        "url='../dep1'), ProjectSpec(name='dep2', url='../dep2', "
        "revision='1-feature')))",
        "DEBUG   git-ws Project(name='dep1', path='dep1', url='../dep1')",
        "WARNING git-ws Clone dep1 has no revision!",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep1').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep1') OK stdout=None stderr=None",
        "DEBUG   git-ws Project(name='dep2', path='dep2', url='../dep2', revision='1-feature')",
        "DEBUG   git-ws run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    git-ws Git('dep2').get_tag() = None",
        "DEBUG   git-ws run(['git', 'branch', '--show-current'], cwd='dep2') OK stdout=b'1-feature\\n' stderr=b''",
        "INFO    git-ws Git('dep2').get_branch() = '1-feature'",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep2').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep2') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(dependencies=(ProjectSpec(name='dep4', url='../dep4', revision='main'),))",
        "DEBUG   git-ws Project(name='dep4', path='dep4', url='../dep4', revision='main')",
        "DEBUG   git-ws run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep4') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    git-ws Git('dep4').get_tag() = None",
        "DEBUG   git-ws run(['git', 'branch', '--show-current'], cwd='dep4') OK stdout=b'main\\n' stderr=b''",
        "INFO    git-ws Git('dep4').get_branch() = 'main'",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep4') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep4').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep4') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(groups=(Group(name='test'),), "
        "defaults=Defaults(revision='main'), dependencies=(ProjectSpec(name='dep3', "
        "url='../dep3', groups=('test',)), ProjectSpec(name='dep4', url='../dep4', "
        "revision='main')))",
        "DEBUG   git-ws FILTERED OUT Project(name='dep3', path='dep3', url='../dep3', "
        "revision='main', groups=(Group(name='test'),))",
        "DEBUG   git-ws DUPLICATE Project(name='dep4', path='dep4', url='../dep4', revision='main')",
    ]


def test_foreach_missing(tmp_path, arepo, caplog):
    """Test foreach."""
    # pylint: disable=unused-argument
    rmtree(tmp_path / "workspace" / "dep2")
    assert cli(["foreach", "git", "status"], exit_code=1) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "Error: Git Clone 'dep2' is missing. Try:",
        "",
        "    git ws update",
        "",
        "",
    ]


def test_foreach_fail(tmp_path, arepo):
    """Test foreach failing."""
    # pylint: disable=unused-argument
    assert cli(["foreach", "--", "git", "status", "--invalidoption"], exit_code=1) == [
        "===== main (MAIN) =====",
        "Error: Command '('git', 'status', '--invalidoption')' returned non-zero exit status 129.",
        "",
    ]


def test_outside(tmp_path, arepo):
    """Outside Workspace."""
    # pylint: disable=unused-argument
    with chdir(tmp_path):
        assert cli(["update"], exit_code=1) == [
            "Error: git workspace has not been initialized yet. Try:",
            "",
            "    git ws init",
            "",
            "or:",
            "",
            "    git ws clone",
            "",
            "",
        ]


def _test_foreach(tmp_path, arepo, *command):
    # pylint: disable=unused-argument
    assert cli(command) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_git_no_color(tmp_path, arepo, caplog):
    """Test git."""
    # pylint: disable=unused-argument
    assert cli(["config", "set", "color_ui", "False"]) == [""]
    assert cli(["git", "status"]) == [
        "===== main (MAIN) =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has no revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert format_logs(caplog, tmp_path) == [
        "INFO    git-ws Workspace path=TMP/workspace main=main "
        "AppConfigData(manifest_path='git-ws.toml', color_ui=False, groups=None)",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='main') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('main').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='main') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(dependencies=(ProjectSpec(name='dep1', "
        "url='../dep1'), ProjectSpec(name='dep2', url='../dep2', "
        "revision='1-feature')))",
        "DEBUG   git-ws Project(name='dep1', path='dep1', url='../dep1')",
        "WARNING git-ws Clone dep1 has no revision!",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep1').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep1') OK stdout=None stderr=None",
        "DEBUG   git-ws Project(name='dep2', path='dep2', url='../dep2', revision='1-feature')",
        "DEBUG   git-ws run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    git-ws Git('dep2').get_tag() = None",
        "DEBUG   git-ws run(['git', 'branch', '--show-current'], cwd='dep2') OK stdout=b'1-feature\\n' stderr=b''",
        "INFO    git-ws Git('dep2').get_branch() = '1-feature'",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep2').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep2') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(dependencies=(ProjectSpec(name='dep4', url='../dep4', revision='main'),))",
        "DEBUG   git-ws Project(name='dep4', path='dep4', url='../dep4', revision='main')",
        "DEBUG   git-ws run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep4') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    git-ws Git('dep4').get_tag() = None",
        "DEBUG   git-ws run(['git', 'branch', '--show-current'], cwd='dep4') OK stdout=b'main\\n' stderr=b''",
        "INFO    git-ws Git('dep4').get_branch() = 'main'",
        "DEBUG   git-ws run(['git', 'rev-parse', '--show-cdup'], cwd='dep4') OK stdout=b'\\n' stderr=b''",
        "INFO    git-ws Git('dep4').is_cloned() = True",
        "DEBUG   git-ws run(('git', 'status'), cwd='dep4') OK stdout=None stderr=None",
        "DEBUG   git-ws ManifestSpec(groups=(Group(name='test'),), "
        "defaults=Defaults(revision='main'), dependencies=(ProjectSpec(name='dep3', "
        "url='../dep3', groups=('test',)), ProjectSpec(name='dep4', url='../dep4', "
        "revision='main')))",
        "DEBUG   git-ws FILTERED OUT Project(name='dep3', path='dep3', url='../dep3', "
        "revision='main', groups=(Group(name='test'),))",
        "DEBUG   git-ws DUPLICATE Project(name='dep4', path='dep4', url='../dep4', revision='main')",
    ]
