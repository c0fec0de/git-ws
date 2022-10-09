"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo, Git
from anyrepo._cli import main

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, format_output


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


def test_status(tmp_path, arepo, caplog):
    """Test status."""
    result = CliRunner().invoke(main, ("status",))
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
    assert result.exit_code == 0


def test_status_modified(tmp_path, arepo, caplog):
    """Test status."""

    workspace = tmp_path / "workspace"
    dep1 = workspace / "dep1"
    dep4 = workspace / "dep4"
    git4 = Git(dep4)

    (dep1 / "foo.txt").touch()
    (dep4 / "foo.txt").touch()
    git4.add(("foo.txt",))

    result = CliRunner().invoke(main, ("status",))
    assert format_output(result) == [
        "===== main =====",
        "===== dep1 =====",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]
    assert result.exit_code == 0

    with chdir(dep1):
        result = CliRunner().invoke(main, ("status",))
        assert format_output(result) == [
            "===== main =====",
            "===== dep1 =====",
            "?? foo.txt",
            "===== dep2 (revision='1-feature') =====",
            "===== dep4 (revision='main') =====",
            "A  ../dep4/foo.txt",
            "",
        ]
        assert result.exit_code == 0
