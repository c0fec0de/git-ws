"""Command Line Interface."""
from shutil import rmtree

from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, format_logs, format_output


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


def test_pull(tmp_path, arepo, caplog):
    """Test pull."""
    _test_foreach(tmp_path, arepo, caplog, "pull")


def test_fetch(tmp_path, arepo, caplog):
    """Test fetch."""
    _test_foreach(tmp_path, arepo, caplog, "fetch")


def test_rebase(tmp_path, arepo, caplog):
    """Test rebase."""
    _test_foreach(tmp_path, arepo, caplog, "rebase")


def test_diff(tmp_path, arepo, caplog):
    """Test diff."""
    _test_foreach(tmp_path, arepo, caplog, "diff")


def test_deinit(tmp_path, arepo, caplog):
    """Test deinit."""
    result = CliRunner().invoke(main, ["deinit"])
    assert format_output(result) == ["Workspace deinitialized at '.'.", ""]

    assert result.exit_code == 0
    assert not (tmp_path / "workspace/.anyrepo").exists()
    assert (tmp_path / "workspace/main").exists()

    result = CliRunner().invoke(main, ["deinit"])
    assert format_output(result, tmp_path) == [
        "Error: anyrepo has not been initialized yet. Try:",
        "",
        "    anyrepo init",
        "",
        "or:",
        "",
        "    anyrepo clone",
        "",
        "",
    ]
    assert result.exit_code == 1


def test_git(tmp_path, arepo):
    """Test git."""
    result = CliRunner().invoke(main, ["git", "status"])
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["git", "status", "-P", "dep2", "-P", "./dep4"])
    assert format_output(result) == [
        "===== SKIPPING main =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0


def test_foreach(tmp_path, arepo, caplog):
    """Test foreach."""
    result = CliRunner().invoke(main, ["foreach", "git", "status"])
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0
    assert format_logs(caplog, tmp_path) == [
        "INFO    anyrepo path=TMP/workspace",
        "INFO    anyrepo Loaded TMP/workspace Info(main_path=PosixPath('main')) "
        "AppConfigData(manifest_path='anyrepo.toml', color_ui=True, groups=None)",
        "INFO    anyrepo run(('git', 'describe', '--exact-match', '--tags'), "
        "cwd='main') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(('git', 'branch', '--show-current'), cwd='main') OK stdout=b'main\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='main') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='main') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep1', "
        "url='../dep1'), ProjectSpec(name='dep2', url='../dep2', "
        "revision='1-feature')))",
        "DEBUG   anyrepo Project(name='dep1', path='dep1', url='../dep1')",
        "INFO    anyrepo run(('git', 'describe', '--exact-match', '--tags'), "
        "cwd='dep1') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(('git', 'branch', '--show-current'), cwd='dep1') OK stdout=b'main\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep1') OK stdout=None stderr=None",
        "DEBUG   anyrepo Project(name='dep2', path='dep2', url='../dep2', revision='1-feature')",
        "INFO    anyrepo run(('git', 'describe', '--exact-match', '--tags'), "
        "cwd='dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(('git', 'branch', '--show-current'), cwd='dep2') OK stdout=b'1-feature\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep2') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep4', url='../dep4', revision='main'),))",
        "DEBUG   anyrepo Project(name='dep4', path='dep4', url='../dep4', revision='main')",
        "INFO    anyrepo run(('git', 'describe', '--exact-match', '--tags'), "
        "cwd='dep4') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(('git', 'branch', '--show-current'), cwd='dep4') OK stdout=b'main\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep4') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep4') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(groups=(Group(name='test'),), "
        "dependencies=(ProjectSpec(name='dep3', url='../dep3', groups=('test',)), "
        "ProjectSpec(name='dep4', url='../dep4', revision='main')))",
        "DEBUG   anyrepo FILTERED OUT Project(name='dep3', path='dep3', "
        "url='../dep3', groups=(Group(name='test'),))",
        "DEBUG   anyrepo DUPLICATE Project(name='dep4', path='dep4', url='../dep4', revision='main')",
    ]


def test_foreach_missing(tmp_path, arepo, caplog):
    """Test foreach."""
    rmtree(tmp_path / "workspace" / "dep2")
    result = CliRunner().invoke(main, ["foreach", "git", "status"])
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "Error: Git Clone 'dep2' is missing. Try:",
        "",
        "    anyrepo update",
        "",
        "",
    ]
    assert result.exit_code == 1


def test_foreach_fail(tmp_path, arepo):
    """Test foreach failing."""
    result = CliRunner().invoke(main, ["foreach", "--", "git", "status", "--invalidoption"])
    assert format_output(result) == [
        "===== main =====",
        "Error: Command '('git', 'status', '--invalidoption')' returned non-zero exit status 129.",
        "",
    ]
    assert result.exit_code == 1


def test_outside(tmp_path, arepo):
    """Outside Workspace."""

    with chdir(tmp_path):
        result = CliRunner().invoke(main, ["update"])
        assert format_output(result) == [
            "Error: anyrepo has not been initialized yet. Try:",
            "",
            "    anyrepo init",
            "",
            "or:",
            "",
            "    anyrepo clone",
            "",
            "",
        ]
        assert result.exit_code == 1


def _test_foreach(tmp_path, arepo, caplog, *command):
    result = CliRunner().invoke(main, command)
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0
