"""Initialization Tests."""
from click.testing import CliRunner

from anyrepo import AnyRepo
from anyrepo.cli import main

from .util import chdir, run


def test_cli_nogit(tmp_path):
    """Init without GIT repo."""
    mainpath = tmp_path / "main"
    mainpath.mkdir(parents=True)
    with chdir(mainpath):
        result = CliRunner().invoke(main, ["init"])
    assert result.exit_code == 1
    assert result.output == "Error: git clone has not been initialized yet (Try 'git init' or 'git clone').\n"


def test_cli_git(tmp_path):
    """Init with GIT repo."""
    mainpath = tmp_path / "main"
    mainpath.mkdir(parents=True)
    with chdir(mainpath):
        run(("git", "init"), check=True)
        assert (mainpath / ".git").exists()
        result = CliRunner().invoke(main, ["init"])
        assert result.exit_code == 0
        assert not result.output

    #     arepo = AnyRepo.init()

    # assert arepo.root_path == tmp_path
    # config_file = arepo.root_path / ".anyrepo"
    # assert config_file.exists()
    # assert config_file.is_file()


def test_git(tmp_path):
    """Init with GIT repo."""
    mainpath = tmp_path / "main"
    mainpath.mkdir(parents=True)
    with chdir(mainpath):
        run(("git", "init"), check=True)
        arepo = AnyRepo.init()

    assert arepo.root_path == tmp_path
    configfile = arepo.root_path / ".anyrepo"
    assert configfile.exists()
    assert configfile.is_file()
