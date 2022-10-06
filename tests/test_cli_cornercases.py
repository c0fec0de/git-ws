"""Command Line Interface."""
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo.datamodel import ManifestSpec, ProjectSpec

from .fixtures import git_repo

# pylint: disable=unused-import,duplicate-code
from .util import chdir, format_logs, format_output, get_sha, run


def check(workspace, name, content=None, exists=True):
    """Check."""
    file_path = workspace / name / "data.txt"
    content = content or name
    if exists:
        assert file_path.exists()
        assert file_path.read_text() == f"{content}"
    else:
        assert not file_path.exists()


@fixture
def repos_deptop(tmp_path):
    """Fixture dep back to top."""

    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "top", commit="initial") as path:
        (path / "data.txt").write_text("top")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep2", url="../dep2"),
            ],
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3", revision="main"),
                ProjectSpec(name="top", url="../top"),
            ]
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3", revision="main"),
            ],
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")
        ManifestSpec(
            dependencies=[
                ProjectSpec(name="top"),
            ],
        ).save(path / "anyrepo.toml")

    yield repos_path


def test_deptop(tmp_path, repos_deptop, caplog):
    """Initialized :any:`AnyRepo` on `repos_deptop`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos_deptop / "top"))

        check(workspace, "top")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)

        arepo.update(skip_main=True)

        check(workspace, "top")
        check(workspace, "dep1")
        check(workspace, "dep2")
        check(workspace, "dep3")

    assert format_logs(caplog, tmp_path) == [
        "INFO    anyrepo run(['git', 'clone', '--', 'TMP/repos/top', "
        "'TMP/workspace/top'], cwd='None') OK stdout=None stderr=None",
        "INFO    anyrepo Initialized TMP/workspace Info(main_path=PosixPath('top')) "
        "AppConfigData(manifest_path='anyrepo.toml', color_ui=True, groups=None)",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='top') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'remote', 'get-url', 'origin'), cwd='top') OK "
        "stdout=b'TMP/repos/top\\n' stderr=b''",
        "DEBUG   anyrepo ManifestSpec(defaults=Defaults(), dependencies=(ProjectSpec(name='dep1', url='../dep1'), "
        "ProjectSpec(name='dep2', url='../dep2')))",
        "DEBUG   anyrepo Project(name='dep1', path='dep1', url='TMP/repos/dep1')",
        "INFO    anyrepo run(['git', 'clone', '--', 'TMP/repos/dep1', 'dep1'], cwd='None') OK stdout=None stderr=None",
        "DEBUG   anyrepo Project(name='dep2', path='dep2', url='TMP/repos/dep2')",
        "INFO    anyrepo run(['git', 'clone', '--', 'TMP/repos/dep2', 'dep2'], cwd='None') OK stdout=None stderr=None",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep1') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'remote', 'get-url', 'origin'), cwd='dep1') OK "
        "stdout=b'TMP/repos/dep1\\n' stderr=b''",
        "DEBUG   anyrepo ManifestSpec(defaults=Defaults(), "
        "dependencies=(ProjectSpec(name='dep3', url='../dep3', revision='main'), "
        "ProjectSpec(name='top', url='../top')))",
        "DEBUG   anyrepo Project(name='dep3', path='dep3', url='TMP/repos/dep3', revision='main')",
        "INFO    anyrepo run(['git', 'clone', '--branch', 'main', '--', "
        "'TMP/repos/dep3', 'dep3'], cwd='None') OK stdout=None stderr=None",
        "DEBUG   anyrepo DUPLICATE Project(name='top', path='top', url='TMP/repos/top')",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep3') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'remote', 'get-url', 'origin'), cwd='dep3') OK "
        "stdout=b'TMP/repos/dep3\\n' stderr=b''",
        "DEBUG   anyrepo ManifestSpec(defaults=Defaults(), dependencies=(ProjectSpec(name='top'),))",
        "DEBUG   anyrepo DUPLICATE Project(name='top', path='top', url='TMP/repos/top')",
        "INFO    anyrepo run(('git', 'rev-parse', '--show-cdup'), cwd='dep2') OK stdout=b'\\n' stderr=b''",
        "INFO    anyrepo run(('git', 'remote', 'get-url', 'origin'), cwd='dep2') OK "
        "stdout=b'TMP/repos/dep2\\n' stderr=b''",
        "DEBUG   anyrepo ManifestSpec(defaults=Defaults(), "
        "dependencies=(ProjectSpec(name='dep3', url='../dep3', revision='main'),))",
        "DEBUG   anyrepo DUPLICATE Project(name='dep3', path='dep3', url='TMP/repos/dep3', revision='main')",
    ]
