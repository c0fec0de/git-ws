"""Clone Testing."""
from click.testing import CliRunner

from anyrepo import AnyRepo, Group, Manifest, Project
from anyrepo._cli import main

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir


def check(workspace, name, content=None, exists=True):
    """Check."""
    file_path = workspace / name / "data.txt"
    content = content or name
    if exists:
        assert file_path.exists()
        assert file_path.read_text() == f"{content}"
    else:
        assert not file_path.exists()


def test_cli_clone(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        result = CliRunner().invoke(main, ["clone", str(repos / "main")])
        assert result.output.split("\n") == [
            "===== main (revision=None, path='main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    anyrepo update",
            "",
            "",
        ]
        assert result.exit_code == 0

    check(workspace, "main")
    check(workspace, "dep1", exists=False)
    check(workspace, "dep2", exists=False)
    check(workspace, "dep3", exists=False)
    check(workspace, "dep4", exists=False)
    check(workspace, "dep5", exists=False)


def test_cli_clone_update(tmp_path, repos):
    """Cloning via CLI."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        result = CliRunner().invoke(main, ["clone", str(repos / "main"), "--update"])
        assert result.output.split("\n") == [
            "===== main (revision=None, path='main') =====",
            f"Cloning '{tmp_path}/repos/main'.",
            "===== dep1 (revision=None, path='dep1') =====",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== dep2 (revision='1-feature', path='dep2') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== dep4 (revision='main', path='dep4') =====",
            f"Cloning '{tmp_path}/repos/dep4'.",
            "",
        ]
        assert result.exit_code == 0

    check(workspace, "main")
    check(workspace, "dep1")
    check(workspace, "dep2", content="dep2-feature")
    check(workspace, "dep3", exists=False)
    check(workspace, "dep4")
    check(workspace, "dep5", exists=False)


def test_cli_clone_groups(tmp_path, repos):
    """Cloning via CLI with groups."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        result = CliRunner().invoke(main, ["clone", str(repos / "main"), "-G", "+test"])
        assert result.output.split("\n") == [
            "===== main (revision=None, path='main') =====",
            "Cloning " f"'{tmp_path}/repos/main'.",
            "Workspace initialized at '.'. Please continue with:",
            "",
            "    anyrepo update",
            "",
            "",
        ]
        assert result.exit_code == 0

        check(workspace, "main")
        check(workspace, "dep1", exists=False)
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", exists=False)
        check(workspace, "dep5", exists=False)

        result = CliRunner().invoke(main, ["update"])
        assert result.output.split("\n") == [
            "Groups: '+test'",
            "===== main (revision=None, path='main') =====",
            "Pulling branch 'main'.",
            "===== dep1 (revision=None, path='dep1') =====",
            f"Cloning '{tmp_path}/repos/dep1'.",
            "===== dep2 (revision='1-feature', path='dep2') =====",
            f"Cloning '{tmp_path}/repos/dep2'.",
            "===== dep4 (revision='main', path='dep4') =====",
            f"Cloning '{tmp_path}/repos/dep4'.",
            "===== dep3 (revision=None, path='dep3', groups='test') =====",
            f"Cloning '{tmp_path}/repos/dep3'.",
            "",
        ]
        assert result.exit_code == 0

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)


def test_clone(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = AnyRepo.clone(str(main_path))
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "anyrepo.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo

        assert list(arepo.projects()) == [
            Project(name="main", path="main"),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
        ]
        assert list(arepo.manifests()) == [
            Manifest(
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                ),
                path=str(workspace / "main/anyrepo.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(workspace / "dep1/anyrepo.toml"),
            ),
            Manifest(
                groups=(Group(name="test"),),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", groups=(Group(name="test"),)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2/anyrepo.toml"),
            ),
        ]
        assert list(str(item) for item in arepo.clones()) == [
            "Clone(Project(name='main', path='main'), Git(PosixPath('main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', revision='1-feature'), Git(PosixPath('dep2')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('dep4')))",
        ]


def test_clone_groups(tmp_path, repos):
    """Test Cloning."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = AnyRepo.clone(str(main_path), groups="+test")
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "anyrepo.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3")
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo

        assert list(arepo.projects()) == [
            Project(name="main", path="main"),
            Project(name="dep1", path="dep1", url="../dep1"),
            Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
            Project(name="dep4", path="dep4", url="../dep4", revision="main"),
            Project(name="dep3", path="dep3", url="../dep3", groups=(Group(name="test"),)),
        ]
        assert list(arepo.manifests()) == [
            Manifest(
                dependencies=(
                    Project(name="dep1", path="dep1", url="../dep1"),
                    Project(name="dep2", path="dep2", url="../dep2", revision="1-feature"),
                ),
                path=str(workspace / "main/anyrepo.toml"),
            ),
            Manifest(
                dependencies=(Project(name="dep4", path="dep4", url="../dep4", revision="main"),),
                path=str(workspace / "dep1/anyrepo.toml"),
            ),
            Manifest(
                groups=(Group(name="test"),),
                dependencies=(
                    Project(name="dep3", path="dep3", url="../dep3", groups=(Group(name="test"),)),
                    Project(name="dep4", path="dep4", url="../dep4", revision="main"),
                ),
                path=str(workspace / "dep2/anyrepo.toml"),
            ),
        ]
        assert list(str(item) for item in arepo.clones()) == [
            "Clone(Project(name='main', path='main'), Git(PosixPath('main')))",
            "Clone(Project(name='dep1', path='dep1', url='../dep1'), Git(PosixPath('dep1')))",
            "Clone(Project(name='dep2', path='dep2', url='../dep2', revision='1-feature'), Git(PosixPath('dep2')))",
            "Clone(Project(name='dep4', path='dep4', url='../dep4', revision='main'), Git(PosixPath('dep4')))",
            "Clone(Project(name='dep3', path='dep3', url='../dep3', "
            "groups=(Group(name='test'),)), Git(PosixPath('dep3')))",
        ]


def test_clone_other(tmp_path, repos):
    """Test Clone Other."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        main_path = repos / "main"
        arepo = AnyRepo.clone(str(main_path), manifest_path="other.toml")
        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        rrepo = AnyRepo.from_path()
        assert arepo == rrepo

        arepo.update(manifest_path="anyrepo.toml")
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4")
        check(workspace, "dep5", exists=False)

        arepo.update()
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", content="dep2-feature")
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)

        (workspace / "dep5").touch()

        arepo.update(prune=True)
        assert arepo.get_manifest().path == str(workspace / "main" / "other.toml")

        check(workspace, "main")
        check(workspace, "dep1")
        check(workspace, "dep2", exists=False)
        check(workspace, "dep3", exists=False)
        check(workspace, "dep4", content="dep4-feature")
        check(workspace, "dep5", exists=False)
