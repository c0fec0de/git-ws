"""Clone Testing."""
from click.testing import CliRunner

from anyrepo import AnyRepo
from anyrepo._cli import main

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, format_caplog


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        result = CliRunner().invoke(main, ["clone", str(repos / "main")])
        assert result.output.split("\n") == [
            "===== main (revision=None, path=main) =====",
            f"Cloning {tmp_path}/repos/main.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    anyrepo update",
            "",
            "",
        ]
        assert result.exit_code == 0


def test_clone(tmp_path, repos, caplog):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        assert format_caplog(tmp_path, caplog) == [
            "run(['git', 'clone', '--', 'WORK/repos/main', "
            "'WORK/workspace/main'], cwd=None) OK stdout=None stderr=None",
            "Initialized WORK/workspace main anyrepo.toml",
            "run(('git', 'rev-parse', '--show-cdup'), cwd=main) OK stdout=b'\\n' stderr=b''",
            "run(('git', 'remote', 'get-url', 'origin'), cwd=main) OK stdout=b'WORK/repos/main\\n' stderr=b''",
            "Manifest(defaults=Defaults(), remotes=[], "
            "dependencies=[ProjectSpec(name='dep1', url='../dep1'), "
            "ProjectSpec(name='dep2', url='../dep2')])",
            "Project(name='dep1', path='dep1', url='WORK/repos/dep1')",
            "run(['git', 'clone', '--', 'WORK/repos/dep1', 'dep1'], cwd=None) OK stdout=None stderr=None",
            "Project(name='dep2', path='dep2', url='WORK/repos/dep2')",
            "run(['git', 'clone', '--', 'WORK/repos/dep2', 'dep2'], cwd=None) OK stdout=None stderr=None",
            "run(('git', 'rev-parse', '--show-cdup'), cwd=dep1) OK stdout=b'\\n' stderr=b''",
            "run(('git', 'remote', 'get-url', 'origin'), cwd=dep1) OK stdout=b'WORK/repos/dep1\\n' stderr=b''",
            "Manifest(defaults=Defaults(), remotes=[], dependencies=[ProjectSpec(name='dep4', url='../dep4')])",
            "Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
            "run(['git', 'clone', '--', 'WORK/repos/dep4', 'dep4'], cwd=None) OK stdout=None stderr=None",
            "run(('git', 'rev-parse', '--show-cdup'), cwd=dep2) OK stdout=b'\\n' stderr=b''",
            "run(('git', 'remote', 'get-url', 'origin'), cwd=dep2) OK stdout=b'WORK/repos/dep2\\n' stderr=b''",
            "Manifest(defaults=Defaults(), remotes=[], "
            "dependencies=[ProjectSpec(name='dep3', url='../dep3'), "
            "ProjectSpec(name='dep4', url='../dep4')])",
            "Project(name='dep3', path='dep3', url='WORK/repos/dep3')",
            "run(['git', 'clone', '--', 'WORK/repos/dep3', 'dep3'], cwd=None) OK stdout=None stderr=None",
            "DUPLICATE Project(name='dep4', path='dep4', url='WORK/repos/dep4')",
        ]

        for name in ("main", "dep1", "dep2", "dep3", "dep4"):
            file_path = workspace / name / "data.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"{name}"

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo
