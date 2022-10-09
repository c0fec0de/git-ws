"""Command Line Interface."""
from pytest import fixture

from anyrepo import AnyRepo, Git

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli, format_output


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`AnyRepo` on `repos`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = AnyRepo.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


def test_status(tmp_path, arepo):
    """Test status."""
    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_full(tmp_path, arepo):
    """Test Full Workflow."""

    workspace = tmp_path / "workspace"
    dep1 = workspace / "dep1"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"
    git2 = Git(dep2)
    git4 = Git(dep4)

    git2.set_config("user.email", "you@example.com")
    git2.set_config("user.name", "you")
    git4.set_config("user.email", "you@example.com")
    git4.set_config("user.name", "you")

    (dep1 / "foo.txt").touch()
    (dep2 / "bb.txt").touch()
    (dep4 / "foo.txt").touch()
    git4.add(("foo.txt",))

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    with chdir(dep1):
        assert cli(("status",)) == [
            "===== main =====",
            "===== dep1 =====",
            "?? foo.txt",
            "===== dep2 (revision='1-feature') =====",
            "?? ../dep2/bb.txt",
            "===== dep4 (revision='main') =====",
            "A  ../dep4/foo.txt",
            "",
        ]

    assert cli(("add", "dep2/bb.txt", "dep1/foo.txt", "missing/file.txt"), exit_code=1) == [
        "Error: 'missing/file.txt' cannot be associated with any clone.",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("add", "dep2/bb.txt", "dep1/foo.txt")) == [""]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "A  dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("commit", "dep2/bb.txt", "dep4/foo.txt", "-m", "messi")) == [
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("reset", "dep1/foo.txt")) == [""]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]
