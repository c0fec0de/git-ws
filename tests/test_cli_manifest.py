"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main

# pylint: disable=unused-import,duplicate-code
from .fixtures import repos
from .util import chdir, format_output, get_sha, run


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        yield arepo


def test_validate(tmp_path, arepo):
    """Manifest Validate."""
    result = CliRunner().invoke(main, ["manifest", "validate"])
    assert format_output(result) == [""]
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
    assert format_output(result) == [
        "Error: Manifest 'main/anyrepo.toml' is broken: 1 validation error for ManifestSpec",
        "dependencies -> 0 -> name",
        "  field required (type=value_error.missing)",
        "",
    ]
    assert result.exit_code == 1


def test_freeze(tmp_path, arepo):
    """Manifest Freeze."""
    sha1 = get_sha(arepo.path / "dep1")
    sha2 = get_sha(arepo.path / "dep2")
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
    ]

    # STDOUT
    result = CliRunner().invoke(main, ["manifest", "freeze", "-G", "+test"])
    assert format_output(result) == [
        "Error: Git Clone 'dep3' is missing. Try:",
        "",
        "    anyrepo update",
        "",
        "",
    ]
    assert result.exit_code == 1
    CliRunner().invoke(main, ["update", "-G", "+test"])
    result = CliRunner().invoke(main, ["manifest", "freeze", "-G", "+test"])
    assert format_output(result) == lines + [
        "[[dependencies]]",
        'name = "dep3"',
        'url = "../dep3"',
        'revision = "v1.0"',
        'path = "dep3"',
        'groups = ["test"]',
        "",
        "",
    ]
    assert result.exit_code == 0

    # FILE
    output_path = tmp_path / "manifest.toml"
    result = CliRunner().invoke(main, ["manifest", "freeze", "--output", str(output_path)])
    assert format_output(result) == [
        "",
    ]
    assert result.exit_code == 0
    assert output_path.read_text().split("\n") == lines

    result = CliRunner().invoke(main, ["update", "--manifest", str(output_path)])
    assert format_output(result) == [
        "===== main (revision=None, path='main') =====",
        "Pulling branch 'main'.",
        f"===== dep1 (revision={sha1!r}, path='dep1') =====",
        "Fetching.",
        f"Checking out {sha1!r} (previously 'main').",
        f"===== dep2 (revision={sha2!r}, path='dep2') =====",
        "Fetching.",
        f"Checking out {sha2!r} (previously '1-feature').",
        f"===== dep4 (revision={sha4!r}, path='dep4') =====",
        "Fetching.",
        f"Checking out {sha4!r} (previously 'main').",
        "",
    ]
    assert result.exit_code == 0

    # STDOUT again
    result = CliRunner().invoke(main, ["manifest", "freeze"])
    assert format_output(result) == lines + [""]
    assert result.exit_code == 0

    result = CliRunner().invoke(main, ["update", "--manifest", str(output_path)])
    assert format_output(result) == [
        "===== main (revision=None, path='main') =====",
        "Pulling branch 'main'.",
        f"===== dep1 (revision={sha1!r}, path='dep1') =====",
        "Nothing to do.",
        f"===== dep2 (revision={sha2!r}, path='dep2') =====",
        "Nothing to do.",
        f"===== dep4 (revision={sha4!r}, path='dep4') =====",
        "Nothing to do.",
        "",
    ]
    assert result.exit_code == 0


def test_resolve(tmp_path, arepo):
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
    ]

    # STDOUT
    result = CliRunner().invoke(main, ["manifest", "resolve"])
    assert format_output(result) == lines + [""]
    assert result.exit_code == 0

    # FILE
    output_path = tmp_path / "manifest.toml"
    result = CliRunner().invoke(main, ["manifest", "resolve", "--output", str(output_path)])
    assert format_output(result) == [
        "",
    ]
    assert result.exit_code == 0
    assert output_path.read_text().split("\n") == lines


def test_path(tmp_path, arepo):
    """Manifest Path."""
    result = CliRunner().invoke(main, ["manifest", "path"])
    main_path = tmp_path / "workspace" / "main" / "anyrepo.toml"
    assert format_output(result) == [
        f"{main_path!s}",
        "",
    ]
    assert result.exit_code == 0


def test_paths(tmp_path, arepo):
    """Manifest Paths."""
    result = CliRunner().invoke(main, ["manifest", "paths"])
    main_path = tmp_path / "workspace" / "main" / "anyrepo.toml"
    dep1_path = tmp_path / "workspace" / "dep1" / "anyrepo.toml"
    dep2_path = tmp_path / "workspace" / "dep2" / "anyrepo.toml"
    assert format_output(result) == [
        f"{main_path!s}",
        f"{dep1_path!s}",
        f"{dep2_path!s}",
        "",
    ]
    assert result.exit_code == 0
