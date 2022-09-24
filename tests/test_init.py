"""Initialization Tests."""
# from click.testing import CliRunner
# from pytest import raises

# from anyrepo import AnyRepo, InitializedError
# from anyrepo.cli import main

# from .util import chdir, run

# def test_cli_nogit(tmp_path):
#     """Init without GIT repo."""
#     mainpath = tmp_path / "main"
#     mainpath.mkdir(parents=True)
#     with chdir(mainpath):
#         result = CliRunner().invoke(main, ["init"])
#     assert result.exit_code == 1


# def test_cli_git(tmp_path):
#     """Init with GIT repo."""
#     mainpath = tmp_path / "main"
#     mainpath.mkdir(parents=True)
#     with chdir(mainpath):
#         run(("git", "init"), check=True)
#         assert (mainpath / ".git").exists()

#         result = CliRunner().invoke(main, ["init"])
#         assert result.exit_code == 1
#         assert result.output.split("\n") == [
#             "Error: Manifest anyrepo.toml has not been found at .",
#             "Try",
#             "",
#             "anyrepo create-manifest --project='.' --manifest='anyrepo.toml'",
#             "",
#         ]

#         result = CliRunner().invoke(main, ["create-manifest"])
#         assert result.exit_code == 0

#         result = CliRunner().invoke(main, ["init"])
#         assert result.exit_code == 0
#         assert not result.output

#         result = CliRunner().invoke(main, ["init"])
#         assert result.exit_code == 1
#         assert result.output== ""


# # def test_git(tmp_path):
# #     """Init with GIT repo."""
# #     mainpath = tmp_path / "main"
#     mainpath.mkdir(parents=True)
#     with chdir(mainpath):
#         run(("git", "init"), check=True)
#         arepo = AnyRepo.init()

#         assert arepo.path == tmp_path
#         infofile = arepo.path / ".anyrepo" / "info.toml"
#         assert infofile.exists()
#         assert infofile.is_file()

#         with raises(InitializedError):
#             AnyRepo.init()
