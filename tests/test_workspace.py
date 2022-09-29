"""Workspace Testing."""
# pylint: disable=duplicate-code
from pathlib import Path

from pytest import raises

from anyrepo import OutsideWorkspaceError, UninitializedError
from anyrepo.const import INFO_PATH
from anyrepo.workspace import Info, Workspace

from .util import chdir, run

TESTDATA = Path(__file__).parent / "testdata"


def test_load():
    """Test Load."""
    workspace_path = TESTDATA / "workspace0"
    workspace = Workspace.from_path(workspace_path / "bar" / "sub")
    assert workspace.path == workspace_path
    assert workspace.info == Info(main_path=Path("bar"), manifest_path="anyrepo.toml")


def test_load_uninit(tmp_path):
    """Test Load Uninitialized."""
    with raises(UninitializedError):
        Workspace.from_path(tmp_path)


def test_init(tmp_path):
    """Initialize."""
    with chdir(tmp_path):
        main_path = tmp_path / "main"
        main_path.mkdir(parents=True)
        run(("git", "init"), check=True)
        workspace = Workspace.init(tmp_path, main_path, manifest_path=Path("resolved.toml"))
        assert workspace.path == tmp_path
        assert workspace.info == Info(main_path=Path("main"), manifest_path="resolved.toml")
        info_file = workspace.path / INFO_PATH
        assert info_file.read_text().split("\n") == [
            "# AnyRepo System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            'manifest_path = "resolved.toml"',
            'groups = ""',
            "",
        ]


def test_outside(tmp_path):
    """Test Outside."""
    with chdir(tmp_path):
        sub_path = tmp_path / "sub"
        sub_path.mkdir(parents=True)
        with raises(OutsideWorkspaceError):
            Workspace.init(sub_path, tmp_path)
