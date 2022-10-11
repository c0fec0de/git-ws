"""Command Line Interface - Update Variants."""
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo.datamodel import ManifestSpec, ProjectSpec

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_output, run


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
    assert cli(["update", "-P", "dep2"]) == [
        "===== SKIPPING main =====",
        "===== SKIPPING dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== SKIPPING dep4 (revision='main') =====",
        "",
    ]

    # Update
    assert cli(["update"], tmp_path=tmp_path) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "anyrepo WARNING Clone dep5 has an empty revision!",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]

    # Update again
    assert cli(["update"]) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "Pulling branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Pulling branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep5 =====",
        "anyrepo WARNING Clone dep5 has an empty revision!",
        "Pulling branch 'main'.",
        "",
    ]

    # Update other.toml
    assert cli(["update", "--manifest", "other.toml"], tmp_path=tmp_path) == [
        "===== main =====",
        "Pulling branch 'main'.",
        "===== dep1 (revision='main') =====",
        "Pulling branch 'main'.",
        "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Merging branch '4-feature'.",
        "",
    ]


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
    assert cli(["update", "--rebase"], tmp_path=tmp_path) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "anyrepo WARNING Clone dep5 has an empty revision!",
        "Cloning 'TMP/repos/dep5'.",
        "",
    ]

    assert cli(["update", "--rebase"]) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep2 (revision='1-feature') =====",
        "Fetching.",
        "Rebasing branch '1-feature'.",
        "===== dep4 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep5 =====",
        "anyrepo WARNING Clone dep5 has an empty revision!",
        "Fetching.",
        "Rebasing branch 'main'.",
        "",
    ]

    assert cli(["update", "--manifest", "other.toml", "--rebase"], tmp_path=tmp_path) == [
        "===== main =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep1 (revision='main') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
        "===== dep6 (revision='main', path='sub/dep6', groups='+foo,+bar,+fast') =====",
        "Cloning 'TMP/repos/dep6'.",
        "===== dep4 (revision='4-feature') =====",
        "Fetching.",
        "Checking out '4-feature' (previously 'main').",
        "Rebasing branch '4-feature'.",
        "",
    ]

    assert cli(["status"]) == [
        "===== main =====",
        "===== dep1 =====",
        "anyrepo WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "anyrepo WARNING Clone dep4 (revision='main') is on different revision: '4-feature'",
        "",
    ]
