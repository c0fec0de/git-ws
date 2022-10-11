"""Command Line Interface."""
from pytest import fixture

from gitws import Git, GitWS

# pylint: disable=unused-import
from .fixtures import repos
from .util import chdir, cli


@fixture
def arepo(tmp_path, repos):
    """Initialized :any:`GitWS` on `repos`."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with chdir(workspace):
        arepo = GitWS.clone(str(repos / "main"))
        arepo.update(skip_main=True)

        yield arepo


def test_status(tmp_path, arepo):
    """Test status."""
    # pylint: disable=unused-argument

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_workflow(tmp_path, arepo):
    """Test Full Workflow."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep1 = workspace / "dep1"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"
    git1 = Git(dep1)
    git2 = Git(dep2)
    git4 = Git(dep4)

    git1.set_config("user.email", "you@example.com")
    git1.set_config("user.name", "you")
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
        "git-ws WARNING Clone dep1 has an empty revision!",
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
            "git-ws WARNING Clone dep1 has an empty revision!",
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
        "git-ws WARNING Clone dep1 has an empty revision!",
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
        "git-ws WARNING Clone dep1 has an empty revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "A  dep2/bb.txt",
        "===== dep4 (revision='main') =====",
        "A  dep4/foo.txt",
        "",
    ]

    assert cli(("commit", "dep2/bb.txt", "dep4/foo.txt"), exit_code=1) == [
        "Error: Please provide a commit message.",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
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
        "git-ws WARNING Clone dep1 has an empty revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("reset", "dep1/foo.txt")) == [""]

    (dep2 / "barbar.txt").touch()

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("commit", "-m", "test")) == [""]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "?? dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("add", "dep1/foo.txt")) == [""]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "A  dep1/foo.txt",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("commit", "-m", "changes")) == ["===== dep1 =====", ""]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "?? dep2/barbar.txt",
        "===== dep4 (revision='main') =====",
        "",
    ]


def test_checkout_file(tmp_path, arepo):
    """Checkout files."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Change")
    (dep4 / "data.txt").write_text("Other Change")

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout", "dep1/missing.txt"), exit_code=1) == [
        "===== main =====",
        "===== dep1 =====",
        "Error: Command '['git', 'checkout', '--', 'missing.txt']' returned non-zero exit status 1.",
        "",
    ]

    assert cli(("checkout", "dep1/data.txt")) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout", "dep2/data.txt")) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]


def test_checkout(tmp_path, arepo):
    """Checkout files."""
    # pylint: disable=unused-argument

    workspace = tmp_path / "workspace"
    dep2 = workspace / "dep2"
    dep4 = workspace / "dep4"

    (dep2 / "data.txt").write_text("My Change")
    (dep4 / "data.txt").write_text("Other Change")

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]

    assert cli(("checkout")) == [
        "===== main =====",
        "===== dep1 =====",
        "===== dep2 (revision='1-feature') =====",
        "===== dep4 (revision='main') =====",
        "",
    ]

    assert cli(("status",)) == [
        "===== main =====",
        "===== dep1 =====",
        "git-ws WARNING Clone dep1 has an empty revision!",
        "===== dep2 (revision='1-feature') =====",
        " M dep2/data.txt",
        "===== dep4 (revision='main') =====",
        " M dep4/data.txt",
        "",
    ]
