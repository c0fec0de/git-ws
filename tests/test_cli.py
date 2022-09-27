"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main
from anyrepo.manifest import Manifest, ProjectSpec

# pylint: disable=unused-import,duplicate-code
from .fixtures import repos
from .util import chdir, format_caplog, run


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

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


def test_status(tmp_path, arepo, caplog):
    """Test status."""
    _test_foreach(tmp_path, arepo, caplog, "status")


def test_update(tmp_path, repos, arepo, caplog):
    """Test update."""

    # Modify dep4
    path = repos / "dep4"
    Manifest(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "anyrepo.toml")
    run(("git", "add", "anyrepo.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Update
    result = CliRunner().invoke(main, ["update"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path=dep1) =====",
        "Pulling.",
        "===== dep2 (revision=None, path=dep2) =====",
        "Pulling.",
        "===== dep4 (revision=None, path=dep4) =====",
        "Pulling.",
        "===== dep5 (revision=None, path=dep5) =====",
        f"Cloning {tmp_path!s}/repos/dep5.",
        "===== dep3 (revision=None, path=dep3) =====",
        "Pulling.",
        "",
    ]
    assert result.exit_code == 0
    assert format_caplog(tmp_path, caplog) == [
        "path=WORK/workspace",
        "Loaded WORK/workspace main anyrepo.toml",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=main) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=main) OK stdout=b'WORK/repos/main\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep1', url='../dep1'), "
        "ProjectSpec(name='dep2', url='../dep2')])",
        "Project(name='dep1', path='dep1', url='WORK/repos/dep1')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep1) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep1) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'pull'), cwd=dep1) OK stdout=None stderr=None",
        "Project(name='dep2', path='dep2', url='WORK/repos/dep2')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep2) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep2) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'pull'), cwd=dep2) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep1) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep1) OK stdout=b'WORK/repos/dep1\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep4) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep4) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'pull'), cwd=dep4) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep4) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep4) OK stdout=b'WORK/repos/dep4\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep5', url='../dep5')])",
        "Project(name='dep5', path='dep5', url='WORK/repos/dep5')",
        "run(['git', 'clone', '--', 'WORK/repos/dep5', 'dep5'], cwd=None) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep2) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep2) OK stdout=b'WORK/repos/dep2\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep3', url='../dep3'), "
        "ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep3', path='dep3', url='WORK/repos/dep3')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep3) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep3) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'pull'), cwd=dep3) OK stdout=None stderr=None",
        "DUPLICATE Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
    ]


def test_update_rebase(tmp_path, repos, arepo, caplog):
    """Test update --rebase."""

    # Modify dep4
    path = repos / "dep4"
    Manifest(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "anyrepo.toml")
    run(("git", "add", "anyrepo.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Fetch
    result = CliRunner().invoke(main, ["fetch"])
    assert result.output.split("\n") == [
        "===== main (revision=None, path=main) =====",
        "git fetch",
        "===== dep1 (revision=None, path=dep1) =====",
        "git fetch",
        "===== dep2 (revision=None, path=dep2) =====",
        "git fetch",
        "===== dep4 (revision=None, path=dep4) =====",
        "git fetch",
        "===== dep3 (revision=None, path=dep3) =====",
        "git fetch",
        "",
    ]
    assert result.exit_code == 0

    # Rebase
    result = CliRunner().invoke(main, ["update", "--rebase"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path=dep1) =====",
        "Rebasing.",
        "===== dep2 (revision=None, path=dep2) =====",
        "Rebasing.",
        "===== dep4 (revision=None, path=dep4) =====",
        "Rebasing.",
        "===== dep5 (revision=None, path=dep5) =====",
        f"Cloning {tmp_path!s}/repos/dep5.",
        "===== dep3 (revision=None, path=dep3) =====",
        "Rebasing.",
        "",
    ]
    assert result.exit_code == 0
    assert format_caplog(tmp_path, caplog) == [
        "path=WORK/workspace",
        "Loaded WORK/workspace main anyrepo.toml",
        "run(('git', 'fetch'), cwd=main) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep1', url='../dep1'), "
        "ProjectSpec(name='dep2', url='../dep2')])",
        "Project(name='dep1', path='dep1', url='../dep1')",
        "run(('git', 'fetch'), cwd=dep1) OK stdout=None stderr=None",
        "Project(name='dep2', path='dep2', url='../dep2')",
        "run(('git', 'fetch'), cwd=dep2) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep4', path='dep4', url='../dep4')",
        "run(('git', 'fetch'), cwd=dep4) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep3', url='../dep3'), "
        "ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep3', path='dep3', url='../dep3')",
        "run(('git', 'fetch'), cwd=dep3) OK stdout=None stderr=None",
        "DUPLICATE Project(name='dep4', path='dep4', url='../dep4')",
        "path=WORK/workspace",
        "Loaded WORK/workspace main anyrepo.toml",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=main) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=main) OK stdout=b'WORK/repos/main\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep1', url='../dep1'), "
        "ProjectSpec(name='dep2', url='../dep2')])",
        "Project(name='dep1', path='dep1', url='WORK/repos/dep1')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep1) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep1) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'rebase'), cwd=dep1) OK stdout=None stderr=None",
        "Project(name='dep2', path='dep2', url='WORK/repos/dep2')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep2) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep2) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'rebase'), cwd=dep2) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep1) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep1) OK stdout=b'WORK/repos/dep1\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep4) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep4) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'rebase'), cwd=dep4) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep4) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep4) OK stdout=b'WORK/repos/dep4\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep5', url='../dep5')])",
        "Project(name='dep5', path='dep5', url='WORK/repos/dep5')",
        "run(['git', 'clone', '--', 'WORK/repos/dep5', 'dep5'], cwd=None) OK stdout=None stderr=None",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep2) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'remote', 'get-url', 'origin'), cwd=dep2) OK stdout=b'WORK/repos/dep2\\n' stderr=b''",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep3', url='../dep3'), "
        "ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep3', path='dep3', url='WORK/repos/dep3')",
        "run(('git', 'rev-parse', '--show-cdup'), cwd=dep3) OK stdout=b'\\n' stderr=b''",
        "run(('git', 'branch', '--show-current'), cwd=dep3) OK stdout=b'main\\n' stderr=b''",
        "run(('git', 'rebase'), cwd=dep3) OK stdout=None stderr=None",
        "DUPLICATE Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
    ]


def test_outside(tmp_path, arepo):
    """Outside Workspace."""

    with chdir(tmp_path):
        result = CliRunner().invoke(main, ["update"])
        assert result.output.split("\n") == [
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


def _test_foreach(tmp_path, arepo, caplog, command):
    result = CliRunner().invoke(main, [command])
    assert result.output.split("\n") == [
        "===== main (revision=None, path=main) =====",
        f"git {command}",
        "===== dep1 (revision=None, path=dep1) =====",
        f"git {command}",
        "===== dep2 (revision=None, path=dep2) =====",
        f"git {command}",
        "===== dep4 (revision=None, path=dep4) =====",
        f"git {command}",
        "===== dep3 (revision=None, path=dep3) =====",
        f"git {command}",
        "",
    ]
    assert result.exit_code == 0
    assert format_caplog(tmp_path, caplog) == [
        "path=WORK/workspace",
        "Loaded WORK/workspace main anyrepo.toml",
        f"run(('git', '{command}'), cwd=main) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep1', url='../dep1'), "
        "ProjectSpec(name='dep2', url='../dep2')])",
        "Project(name='dep1', path='dep1', url='../dep1')",
        f"run(('git', '{command}'), cwd=dep1) OK stdout=None stderr=None",
        "Project(name='dep2', path='dep2', url='../dep2')",
        f"run(('git', '{command}'), cwd=dep2) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep4', path='dep4', url='../dep4')",
        f"run(('git', '{command}'), cwd=dep4) OK stdout=None stderr=None",
        "Manifest(defaults=Defaults(), remotes=[], "
        "dependencies=[ProjectSpec(name='dep3', url='../dep3'), "
        "ProjectSpec(name='dep4', url='../dep4')])",
        "Project(name='dep3', path='dep3', url='../dep3')",
        f"run(('git', '{command}'), cwd=dep3) OK stdout=None stderr=None",
        "DUPLICATE Project(name='dep4', path='dep4', url='../dep4')",
    ]
