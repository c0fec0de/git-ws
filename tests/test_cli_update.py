"""Command Line Interface - Update Variants."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main
from anyrepo.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import,duplicate-code
from .fixtures import repos
from .util import chdir, format_logs, format_output, get_sha, run


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


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
    assert format_output(result) == [
        "===== SKIPPING main =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== SKIPPING dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0

    # Update
    result = CliRunner().invoke(main, ["update"])
    assert format_output(result, tmp_path) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]
    assert result.exit_code == 0

    # Update again
    result = CliRunner().invoke(main, ["update"])
    assert format_output(result) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "Pulling branch 'main'.",
        "",
    ]
    assert result.exit_code == 0

    # Update other.toml
    result = CliRunner().invoke(main, ["update", "--manifest", "other.toml"])
    assert format_output(result, tmp_path) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "Pulling branch 'main'.",
        "===== dep6 (path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
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
    assert format_output(result, tmp_path) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--rebase"])
    assert format_output(result) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "",
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--manifest", "other.toml", "--rebase"])
    assert format_output(result, tmp_path) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep6 (path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Rebasing branch '4-feature'.",
        "",
    ]
    assert result.exit_code == 0
