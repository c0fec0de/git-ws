"""Initialization Tests."""
from click.testing import CliRunner
from pytest import raises

from anyrepo import AnyRepo, InitializedError, ManifestExistError
from anyrepo._cli import main

from .util import chdir, format_output, run


def test_cli_nogit(tmp_path):
    """Init without GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        result = CliRunner().invoke(main, ["init"])
    assert format_output(result) == [
        "Error: git clone has not been found or initialized yet. Change to your existing git clone or try:",
        "",
        "    git init",
        "",
        "or:",
        "",
        "    git clone",
        "",
        "",
    ]
    assert result.exit_code == 1


def test_cli_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 1
        assert format_output(result) == [
            "===== main (revision=None, path='main') =====",
            "Error: Manifest has not been found at 'anyrepo.toml'. Try:",
            "",
            "    anyrepo create-manifest --manifest='anyrepo.toml'",
            "",
            "",
        ]

        result = CliRunner().invoke(main, ["create-manifest"])
        assert format_output(result) == ["Manifest 'anyrepo.toml' created.", ""]
        assert result.exit_code == 0

        manifest_path = main_path / "anyrepo.toml"
        assert manifest_path.read_text().split("\n") == [""]

        result = CliRunner().invoke(main, ["init"])
        assert format_output(result, tmp_path) == [
            "===== main (revision=None, path='main') =====",
            "Workspace initialized at 'TMP'.",
            "Please continue with:",
            "",
            "    anyrepo update",
            "",
            "",
        ]
        assert result.exit_code == 0

        result = CliRunner().invoke(main, ["init"])
        assert format_output(result, tmp_path) == [
            "===== main (revision=None, path='main') =====",
            "Error: anyrepo has already been initialized at 'TMP' with main repo at 'main'.",
            "",
        ]
        assert result.exit_code == 1


def test_cli_git_update(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)
        assert (main_path / ".git").exists()

        result = CliRunner().invoke(main, ["create-manifest"])
        assert format_output(result) == ["Manifest 'anyrepo.toml' created.", ""]
        assert result.exit_code == 0

        manifest_path = main_path / "anyrepo.toml"
        assert manifest_path.read_text().split("\n") == [""]

        result = CliRunner().invoke(main, ["init", "--update"])
        assert format_output(result, tmp_path) == [
            "===== main (revision=None, path='main') =====",
            "Workspace initialized at 'TMP'.",
            "",
        ]
        assert result.exit_code == 0


def test_git(tmp_path):
    """Init with GIT repo."""
    main_path = tmp_path / "main"
    main_path.mkdir(parents=True)
    with chdir(main_path):
        run(("git", "init"), check=True)

        AnyRepo.create_manifest()
        manifest_path = main_path / "anyrepo.toml"
        assert manifest_path.read_text().split("\n") == [""]

        with raises(ManifestExistError):
            AnyRepo.create_manifest()

        arepo = AnyRepo.init()

        assert arepo.path == tmp_path
        info_file = arepo.path / ".anyrepo" / "info.toml"
        assert info_file.read_text().split("\n") == [
            "# AnyRepo System File. DO NOT EDIT.",
            "",
            'main_path = "main"',
            'manifest_path = "anyrepo.toml"',
            'groups = ""',
            "",
        ]

        with raises(InitializedError):
            AnyRepo.init()

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo
