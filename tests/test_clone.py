"""Clone Testing."""
from click.testing import CliRunner

from anyrepo import AnyRepo
from anyrepo._cli import main

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        result = CliRunner().invoke(main, ["clone", str(repos / "main")])
        assert result.output.split("\n") == [
            "===== main (revision=None, path=main) =====",
            f"Cloning {tmp_path}/repos/main.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    anyrepo update",
            "",
            "",
        ]
        assert result.exit_code == 0


def test_clone(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def check(name, content=None):
        file_path = workspace / name / "data.txt"
        content = content or name
        assert file_path.exists()
        assert file_path.read_text() == f"{content}"

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update()

        check("main")
        check("dep1")
        check("dep2", content="dep2-feature")
        check("dep3")
        check("dep4")

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo
