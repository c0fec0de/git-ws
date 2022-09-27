"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main
from anyrepo.manifest import Manifest, ProjectSpec

# pylint: disable=unused-import,duplicate-code
from .fixtures import repos
from .util import chdir, run


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


def test_update(tmp_path, repos, arepo):
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
        "===== dep2 (revision=1-feature, path=dep2) =====",
        "Checking out.",
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


def test_update_rebase(tmp_path, repos, arepo):
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
        "===== dep2 (revision=1-feature, path=dep2) =====",
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
        "===== dep2 (revision=1-feature, path=dep2) =====",
        "Checking out.",
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
        "===== main (revision=None, path=main) =====",
        f"git {command}",
        "===== dep1 (revision=None, path=dep1) =====",
        f"git {command}",
        "===== dep2 (revision=1-feature, path=dep2) =====",
        f"git {command}",
        "===== dep4 (revision=None, path=dep4) =====",
        f"git {command}",
        "===== dep3 (revision=None, path=dep3) =====",
        f"git {command}",
        "",
    ]
    assert result.exit_code == 0
