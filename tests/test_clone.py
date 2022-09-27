"""Clone Testing."""
from anyrepo import AnyRepo

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir


def test_clone(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        for name in ("main", "dep1", "dep2", "dep3", "dep4"):
            file_path = workspace / name / "data.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"{name}"

        # rrepo = AnyRepo.from_path()
        # assert arepo == rrepo
