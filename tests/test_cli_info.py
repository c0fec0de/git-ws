"""Command Line Interface."""
from pytest import fixture

from anyrepo import AnyRepo

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        yield arepo


def test_main_path(tmp_path, arepo):
    """Main Path."""
    # pylint: disable=unused-argument
    assert cli(["info", "main-path"], tmp_path=tmp_path) == ["TMP/workspace/main", ""]


def test_workspace_path(tmp_path, arepo):
    """Workspace Path."""
    # pylint: disable=unused-argument
    assert cli(["info", "workspace-path"], tmp_path=tmp_path) == ["TMP/workspace", ""]


def test_project_paths(tmp_path, arepo):
    """Project Paths."""
    # pylint: disable=unused-argument
    assert cli(["info", "project-paths"], tmp_path=tmp_path) == [
        "TMP/workspace/main",
        "TMP/workspace/dep1",
        "TMP/workspace/dep2",
        "TMP/workspace/dep4",
        "",
    ]
