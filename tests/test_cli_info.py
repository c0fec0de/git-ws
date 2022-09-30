"""Command Line Interface."""
from click.testing import CliRunner
from pytest import fixture

from anyrepo import AnyRepo
from anyrepo._cli import main

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


def test_workspace_path(tmp_path, arepo):
    """Workspace Path."""
    workspace_path = tmp_path / "workspace"
    result = CliRunner().invoke(main, ["info", "workspace-path"])
    assert result.output.split("\n") == [str(workspace_path), ""]
    assert result.exit_code == 0


def test_project_paths(tmp_path, arepo):
    """Project Paths."""
    workspace_path = tmp_path / "workspace"

    result = CliRunner().invoke(main, ["info", "project-paths"])
    paths = ["main", "dep1", "dep2", "dep4"]
    assert result.output.split("\n") == [str(workspace_path / path) for path in paths] + [""]
    assert result.exit_code == 0