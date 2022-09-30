"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main
from anyrepo.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import,duplicate-code
from .fixtures import repos
from .util import chdir, get_sha, run


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        yield arepo


def test_pull(tmp_path, arepo):
    """Test pull."""
    _test_foreach(tmp_path, arepo, "pull")


def test_fetch(tmp_path, arepo):
    """Test fetch."""
    _test_foreach(tmp_path, arepo, "fetch")


def test_rebase(tmp_path, arepo):
    """Test rebase."""
    _test_foreach(tmp_path, arepo, "rebase")


def test_diff(tmp_path, arepo):
    """Test diff."""
    _test_foreach(tmp_path, arepo, "diff")


def test_status(tmp_path, arepo):
    """Test status."""
    _test_foreach(tmp_path, arepo, "status")


def test_git(tmp_path, arepo):
    """Test git."""
    result = CliRunner().invoke(main, ["git", "status"])
    assert result.output.split("\n") == [
        "===== main (revision=None, path='main') =====",
        "git status",
        "===== dep1 (revision=None, path='dep1') =====",
        "git status",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "git status",
        "===== dep4 (revision='main', path='dep4') =====",
        "git status",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["git", "status", "-P", "dep2", "-P", "./dep4"])
    assert result.output.split("\n") == [
        "===== main (revision=None, path='main') =====",
        "SKIPPING",
        "===== dep1 (revision=None, path='dep1') =====",
        "SKIPPING",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "git status",
        "===== dep4 (revision='main', path='dep4') =====",
        "git status",
        "",
    ]
    assert result.exit_code == 0


def test_foreach(tmp_path, arepo):
    """Test foreach."""
    result = CliRunner().invoke(main, ["foreach", "git", "status"])
    assert result.output.split("\n") == [
        "===== main (revision=None, path='main') =====",
        "git status",
        "===== dep1 (revision=None, path='dep1') =====",
        "git status",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "git status",
        "===== dep4 (revision='main', path='dep4') =====",
        "git status",
        "",
    ]
    assert result.exit_code == 0


def test_foreach_fail(tmp_path, arepo):
    """Test foreach failing."""
    result = CliRunner().invoke(main, ["foreach", "--", "git", "status", "--invalidoption"])
    assert result.output.split("\n") == [
        "===== main (revision=None, path='main') =====",
        "git status --invalidoption",
        "Error: Command '('git', 'status', '--invalidoption')' returned non-zero exit status 129.",
        "",
    ]
    assert result.exit_code == 1


def test_update(tmp_path, repos, arepo):
    """Test update."""

    # Modify dep4
    path = repos / "dep4"
    ManifestSpec(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "anyrepo.toml")
    run(("git", "add", "anyrepo.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Update project
    result = CliRunner().invoke(main, ["update", "-P", "dep2"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "SKIPPING",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main', path='dep4') =====",
        "SKIPPING",
        "",
    ]
    assert result.exit_code == 0

    # Update
    result = CliRunner().invoke(main, ["update"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main', path='dep4') =====",
        "Pulling branch 'main'.",
        "===== dep5 (revision=None, path='dep5') =====",
        f"Cloning '{tmp_path!s}/repos/dep5'.",
        "",
    ]
    assert result.exit_code == 0

    # Update again
    result = CliRunner().invoke(main, ["update"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main', path='dep4') =====",
        "Pulling branch 'main'.",
        "===== dep5 (revision=None, path='dep5') =====",
        "Pulling branch 'main'.",
        "",
    ]
    assert result.exit_code == 0

    # Update other.toml
    result = CliRunner().invoke(main, ["update", "--manifest", "other.toml"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Pulling branch 'main'.",
        "===== dep6 (revision=None, path='sub/dep6', groups='+foo,+bar,+fast') =====",
        f"Cloning '{tmp_path}/repos/dep6'.",
        "===== dep4 (revision='4-feature', path='dep4') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Merging branch '4-feature'.",
        "",
    ]
    assert result.exit_code == 0


def test_update_rebase(tmp_path, repos, arepo):
    """Test update --rebase."""

    # Modify dep4
    path = repos / "dep4"
    ManifestSpec(
        dependencies=[
            ProjectSpec(name="dep5", url="../dep5"),
        ]
    ).save(path / "anyrepo.toml")
    run(("git", "add", "anyrepo.toml"), check=True, cwd=path)
    run(("git", "commit", "-m", "adapt dep"), check=True, cwd=path)

    # Rebase
    result = CliRunner().invoke(main, ["update", "--rebase"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main', path='dep4') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 (revision=None, path='dep5') =====",
        f"Cloning '{tmp_path!s}/repos/dep5'.",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--rebase"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main', path='dep4') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 (revision=None, path='dep5') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--manifest", "other.toml", "--rebase"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep6 (revision=None, path='sub/dep6', groups='+foo,+bar,+fast') =====",
        f"Cloning '{tmp_path}/repos/dep6'.",
        "===== dep4 (revision='4-feature', path='dep4') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Rebasing branch '4-feature'.",
        "",
    ]
    assert result.exit_code == 0


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


def _test_foreach(tmp_path, arepo, command):
    result = CliRunner().invoke(main, [command])
    assert result.output.split("\n") == [
        "===== main (revision=None, path='main') =====",
        f"git {command}",
        "===== dep1 (revision=None, path='dep1') =====",
        f"git {command}",
        "===== dep2 (revision='1-feature', path='dep2') =====",
        f"git {command}",
        "===== dep4 (revision='main', path='dep4') =====",
        f"git {command}",
        "",
    ]
    assert result.exit_code == 0
