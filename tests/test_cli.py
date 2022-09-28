"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main
from anyrepo.manifest import ManifestSpec, ProjectSpec

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
        "===== dep3 (revision=None, path='dep3') =====",
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
        "===== dep3 (revision=None, path='dep3') =====",
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
        "===== dep3 (revision=None, path='dep3') =====",
        "Pulling branch 'main'.",
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
        "===== dep3 (revision=None, path='dep3') =====",
        "Pulling branch 'main'.",
        "",
    ]
    assert result.exit_code == 0

    # Update other.toml
    result = CliRunner().invoke(main, ["update", "--manifest", "other.toml"])
    assert result.output.split("\n") == [
        "===== dep1 (revision=None, path='dep1') =====",
        "Pulling branch 'main'.",
        "===== dep6 (revision=None, path='sub/dep6') =====",
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
        "===== dep3 (revision=None, path='dep3') =====",
        "Fetching.",
        "Rebasing branch 'main'.",
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
        "===== dep3 (revision=None, path='dep3') =====",
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
        "===== dep6 (revision=None, path='sub/dep6') =====",
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
        "===== dep3 (revision=None, path='dep3') =====",
        f"git {command}",
        "",
    ]
    assert result.exit_code == 0


def test_manifest_validate(tmp_path, arepo):
    """Manifest Validate."""
    result = CliRunner().invoke(main, ["manifest", "validate"])
    assert result.output.split("\n") == [""]
    assert result.exit_code == 0

    manifest_path = tmp_path / "workspace" / "main" / "anyrepo.toml"
    assert manifest_path.write_text(
        "\n".join(
            [
                "[[dependencies]]",
                'nam = "dep1"',
                "",
                "[[dependencies]]",
                'name = "dep2"',
                'url = "../dep2"',
                'revision = "1-feature"',
                "",
            ]
        )
    )
    result = CliRunner().invoke(main, ["manifest", "validate"])
    assert result.output.split("\n") == [
        "Error: Manifest main/anyrepo.toml is broken: 1 validation error for ManifestSpec",
        "dependencies -> 0 -> name",
        "  field required (type=value_error.missing)",
        "",
    ]
    assert result.exit_code == 1


def test_manifest_freeze(tmp_path, arepo):
    """Manifest Freeze."""
    sha1 = get_sha(arepo.path / "dep1")
    sha2 = get_sha(arepo.path / "dep2")
    sha3 = "v1.0"
    sha4 = get_sha(arepo.path / "dep4")
    lines = [
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        f'revision = "{sha1}"',
        'path = "dep1"',
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        f'revision = "{sha2}"',
        'path = "dep2"',
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        f'revision = "{sha4}"',
        'path = "dep4"',
        "",
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        f'revision = "{sha3}"',
        'path = "dep3"',
        "",
    ]

    # STDOUT
    result = CliRunner().invoke(main, ["manifest", "freeze"])
    assert result.output.split("\n") == lines + [""]
    assert result.exit_code == 0

    # FILE
    output_path = tmp_path / "manifest.toml"
    result = CliRunner().invoke(main, ["manifest", "freeze", "--output", str(output_path)])
    assert result.output.split("\n") == [
        "",
    ]
    assert result.exit_code == 0
    assert output_path.read_text().split("\n") == lines

    result = CliRunner().invoke(main, ["update", "--manifest", str(output_path)])
    assert result.output.split("\n") == [
        f"===== dep1 (revision={sha1!r}, path='dep1') =====",
        "Fetching.",
        f"Checking out {sha1!r} (previously 'main').",
        f"===== dep2 (revision={sha2!r}, path='dep2') =====",
        "Fetching.",
        f"Checking out {sha2!r} (previously '1-feature').",
        f"===== dep4 (revision={sha4!r}, path='dep4') =====",
        "Fetching.",
        f"Checking out {sha4!r} (previously 'main').",
        f"===== dep3 (revision={sha3!r}, path='dep3') =====",
        "Fetching.",
        f"Checking out {sha3!r} (previously 'main').",
        "",
    ]
    assert result.exit_code == 0

    # STDOUT again
    result = CliRunner().invoke(main, ["manifest", "freeze"])
    assert result.output.split("\n") == lines + [""]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--manifest", str(output_path)])
    assert result.output.split("\n") == [
        f"===== dep1 (revision={sha1!r}, path='dep1') =====",
        "Nothing to do.",
        f"===== dep2 (revision={sha2!r}, path='dep2') =====",
        "Nothing to do.",
        f"===== dep4 (revision={sha4!r}, path='dep4') =====",
        "Nothing to do.",
        f"===== dep3 (revision={sha3!r}, path='dep3') =====",
        "Nothing to do.",
        "",
    ]
    assert result.exit_code == 0


def test_manifest_resolve(tmp_path, arepo):
    """Manifest Resolve."""
    lines = [
        "[[dependencies]]",
        'name = "dep1"',
        'url = "../dep1"',
        'path = "dep1"',
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "../dep2"',
        'revision = "1-feature"',
        'path = "dep2"',
        "",
        "[[dependencies]]",
        'name = "dep4"',
        'url = "../dep4"',
        'revision = "main"',
        'path = "dep4"',
        "",
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        'path = "dep3"',
        "",
    ]

    # STDOUT
    result = CliRunner().invoke(main, ["manifest", "resolve"])
    assert result.output.split("\n") == lines + [""]
    assert result.exit_code == 0

    # FILE
    output_path = tmp_path / "manifest.toml"
    result = CliRunner().invoke(main, ["manifest", "resolve", "--output", str(output_path)])
    assert result.output.split("\n") == [
        "",
    ]
    assert result.exit_code == 0
    assert output_path.read_text().split("\n") == lines


def test_manifest_path(tmp_path, arepo):
    """Manifest Path."""
    result = CliRunner().invoke(main, ["manifest", "path"])
    main_path = tmp_path / "workspace" / "main" / "anyrepo.toml"
    assert result.output.split("\n") == [
        f"{main_path!s}",
        "",
    ]
    assert result.exit_code == 0


def test_manifest_paths(tmp_path, arepo):
    """Manifest Paths."""
    result = CliRunner().invoke(main, ["manifest", "paths"])
    main_path = tmp_path / "workspace" / "main" / "anyrepo.toml"
    dep1_path = tmp_path / "workspace" / "dep1" / "anyrepo.toml"
    dep2_path = tmp_path / "workspace" / "dep2" / "anyrepo.toml"
    assert result.output.split("\n") == [
        f"{main_path!s}",
        f"{dep1_path!s}",
        f"{dep2_path!s}",
        "",
    ]
    assert result.exit_code == 0
