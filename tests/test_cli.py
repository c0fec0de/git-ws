"""Command Line Interface."""
from shutil import rmtree

from pytest import fixture

from anyrepo import AnyRepo

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_logs


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


def test_push(tmp_path, arepo, caplog):
    """Test push."""
    _test_foreach(tmp_path, arepo, caplog, "push")


def test_fetch(tmp_path, arepo, caplog):
    """Test fetch."""
    _test_foreach(tmp_path, arepo, caplog, "fetch")


def test_rebase(tmp_path, arepo, caplog):
    """Test rebase."""
    _test_foreach(tmp_path, arepo, caplog, "rebase")


def test_diff(tmp_path, arepo, caplog):
    """Test diff."""
    _test_foreach(tmp_path, arepo, caplog, "diff")


def test_deinit(tmp_path, arepo):
    """Test deinit."""
    assert cli(["deinit"]) == ["Workspace deinitialized at '.'.", ""]

    assert not (tmp_path / "workspace/.anyrepo").exists()
    assert (tmp_path / "workspace/main").exists()

    assert cli(["deinit"], exit_code=1) == [
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


def test_git(tmp_path, arepo):
    """Test git."""
    assert cli(["git", "status"]) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(["git", "status", "-P", "dep2", "-P", "./dep4"]) == [
        "===== SKIPPING main =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_foreach(tmp_path, arepo, caplog):
    """Test foreach."""
    assert cli(["foreach", "git", "status"]) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert format_logs(caplog, tmp_path) == [
        "INFO    anyrepo path=TMP/workspace",
        "INFO    anyrepo Loaded TMP/workspace Info(main_path=PosixPath('main')) "
        "AppConfigData(manifest_path='anyrepo.toml', color_ui=True, groups=None)",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='main') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='main') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep1', "
        "url='../dep1'), ProjectSpec(name='dep2', url='../dep2', "
        "revision='1-feature')))",
        "DEBUG   anyrepo Project(name='dep1', path='dep1', url='../dep1')",
        "WARNING anyrepo Clone dep1 has an empty revision!",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep1') OK stdout=None stderr=None",
        "DEBUG   anyrepo Project(name='dep2', path='dep2', url='../dep2', revision='1-feature')",
        "INFO    anyrepo run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(['git', 'branch', '--show-current'], cwd='dep2') OK stdout=b'1-feature\\n' stderr=b''",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep2') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep4', url='../dep4', revision='main'),))",
        "DEBUG   anyrepo Project(name='dep4', path='dep4', url='../dep4', revision='main')",
        "INFO    anyrepo run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep4') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(['git', 'branch', '--show-current'], cwd='dep4') OK stdout=b'main\\n' stderr=b''",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep4') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep4') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(groups=(Group(name='test'),), "
        "defaults=Defaults(revision='main'), dependencies=(ProjectSpec(name='dep3', "
        "url='../dep3', groups=('test',)), ProjectSpec(name='dep4', url='../dep4', "
        "revision='main')))",
        "DEBUG   anyrepo FILTERED OUT Project(name='dep3', path='dep3', "
        "url='../dep3', revision='main', groups=(Group(name='test'),))",
        "DEBUG   anyrepo DUPLICATE Project(name='dep4', path='dep4', url='../dep4', revision='main')",
    ]


def test_foreach_missing(tmp_path, arepo, caplog):
    """Test foreach."""
    rmtree(tmp_path / "workspace" / "dep2")
    assert cli(["foreach", "git", "status"], exit_code=1) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "Error: Git Clone 'dep2' is missing. Try:",
        "",
        "    anyrepo update",
        "",
        "",
    ]


def test_foreach_fail(tmp_path, arepo):
    """Test foreach failing."""
    assert cli(["foreach", "--", "git", "status", "--invalidoption"], exit_code=1) == [
        "===== main =====",
        "Error: Command '('git', 'status', '--invalidoption')' returned non-zero exit status 129.",
        "",
    ]


def test_outside(tmp_path, arepo):
    """Outside Workspace."""

    with chdir(tmp_path):
        assert cli(["update"], exit_code=1) == [
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


def _test_foreach(tmp_path, arepo, caplog, *command):
    assert cli(command) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_git_no_color(tmp_path, arepo, caplog):
    """Test git."""
    assert cli(["config", "set", "color_ui", "False"]) == [""]
    assert cli(["git", "status"]) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert format_logs(caplog, tmp_path) == [
        "INFO    anyrepo path=TMP/workspace",
        "INFO    anyrepo Loaded TMP/workspace Info(main_path=PosixPath('main')) "
        "AppConfigData(manifest_path='anyrepo.toml', color_ui=False, groups=None)",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='main') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='main') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep1', "
        "url='../dep1'), ProjectSpec(name='dep2', url='../dep2', "
        "revision='1-feature')))",
        "DEBUG   anyrepo Project(name='dep1', path='dep1', url='../dep1')",
        "WARNING anyrepo Clone dep1 has an empty revision!",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep1') OK stdout=None stderr=None",
        "DEBUG   anyrepo Project(name='dep2', path='dep2', url='../dep2', revision='1-feature')",
        "INFO    anyrepo run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep2') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(['git', 'branch', '--show-current'], cwd='dep2') OK stdout=b'1-feature\\n' stderr=b''",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep2') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(dependencies=(ProjectSpec(name='dep4', url='../dep4', revision='main'),))",
        "DEBUG   anyrepo Project(name='dep4', path='dep4', url='../dep4', revision='main')",
        "INFO    anyrepo run(['git', 'describe', '--exact-match', '--tags'], "
        "cwd='dep4') OK stdout=b'' stderr=b'fatal: No names found, cannot describe "
        "anything.\\n'",
        "INFO    anyrepo run(['git', 'branch', '--show-current'], cwd='dep4') OK stdout=b'main\\n' stderr=b''",
        "INFO    anyrepo run(['git', 'rev-parse', '--show-cdup'], cwd='dep4') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'status'), cwd='dep4') OK stdout=None stderr=None",
        "DEBUG   anyrepo ManifestSpec(groups=(Group(name='test'),), "
        "defaults=Defaults(revision='main'), dependencies=(ProjectSpec(name='dep3', "
        "url='../dep3', groups=('test',)), ProjectSpec(name='dep4', url='../dep4', "
        "revision='main')))",
        "DEBUG   anyrepo FILTERED OUT Project(name='dep3', path='dep3', "
        "url='../dep3', revision='main', groups=(Group(name='test'),))",
        "DEBUG   anyrepo DUPLICATE Project(name='dep4', path='dep4', url='../dep4', revision='main')",
    ]
