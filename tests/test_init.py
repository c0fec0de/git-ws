"""Initialization Tests."""
from click.testing import CliRunner
from pytest import raises

from anyrepo import AnyRepo, InitializedError, ManifestExistError
from anyrepo.cli import main

from .util import chdir, run


def test_cli_nogit(tmp_path):
    """Init without GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        result = CliRunner().invoke(main, ["init"])
    assert result.exit_code == 1
    assert result.output.split("\n") == [
        "Error: git clone has not been initialized yet.",
        "Try:",
        "",
        "git init",
        "",
        "or:",
        "",
        "git clone",
        "",
    ]


def test_cli_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 1
        assert result.output.split("\n") == [
            "Error: Manifest has not been found at anyrepo.yaml",
            "Try",
            "",
            "anyrepo create-manifest --manifest='anyrepo.yaml'",
            "",
        ]

        result = CliRunner().invoke(main, ["create-manifest"])
        assert result.exit_code == 0
        assert result.output.split("\n") == ["Manifest anyrepo.yaml created.", ""]

        manifest_path = main_path / "anyrepo.yaml"
        assert manifest_path.read_text().split("\n") == [
            "manifest:",
            "  defaults: {}",
            "  projects: []",
            "  remotes: []",
            "  self:",
            "    name: main",
            "    revision: master",
            "",
        ]

        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 0
        assert result.output.split("\n") == [f"Workspace initialized at {tmp_path!s}", ""]

        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 1
        assert result.output.split("\n") == [
            f"Error: anyrepo has already been initialized yet at {tmp_path!s}.",
            "",
        ]


def test_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)

        AnyRepo.create_manifest()
        manifest_path = main_path / "anyrepo.yaml"
        assert manifest_path.read_text().split("\n") == [
            "manifest:",
            "  defaults: {}",
            "  projects: []",
            "  remotes: []",
            "  self:",
            "    name: main",
            "    revision: master",
            "",
        ]
        with raises(ManifestExistError):
            AnyRepo.create_manifest()

        arepo = AnyRepo.init()

        assert arepo.path == tmp_path
        info_file = arepo.path / ".anyrepo" / "info.yaml"
        assert info_file.read_text().split("\n") == [
            "main_path: main",
            "manifest_path: anyrepo.yaml",
            "",
        ]

        with raises(InitializedError):
            AnyRepo.init()
