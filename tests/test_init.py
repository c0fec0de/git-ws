import pathlib

from pytest import raises

from anyrepo import AnyRepo, NoGitError

from .util import chdir, run


def test_nogit(tmp_path):
    """Init without GIT repo."""
    mainpath = tmp_path / "main"
    mainpath.mkdir(parents=True)
    with chdir(mainpath):
        with raises(NoGitError):
            AnyRepo.init()


def test_git(tmp_path):
    """Init with GIT repo."""
    mainpath = tmp_path / "main"
    mainpath.mkdir(parents=True)
    with chdir(mainpath):
        run(("git", "init"))
        arepo = AnyRepo.init()

    assert arepo.rootpath == tmp_path
    configfile = arepo.rootpath / ".anyrepo"
    assert configfile.exists()
    assert configfile.is_file()
