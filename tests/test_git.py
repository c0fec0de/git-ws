"""Git Testing."""
import re

from pytest import fixture

from anyrepo._git import Git


def is_sha(sha):
    """Return if result is a SHA."""
    return re.match(r"^[0-9a-fA-F]+$", sha) is not None


@fixture
def git(tmp_path) -> Git:
    """Testfixture with initialized GIT repo."""
    git = Git(tmp_path)
    assert not git.is_cloned()
    git.init(branch="main")
    git.set_config("user.email", "you@example.com")
    git.set_config("user.name", "you")
    return git


def test_git(git):
    """GIT testing."""
    assert git.is_cloned()
    assert git.get_url() is None
    path = git.path

    (path / "data.txt").touch()
    git.add("data.txt")
    git.commit("initial")


def test_git_revisions(git):
    """Git Versioning."""
    # on branch, sha0
    path = git.path
    (path / "data.txt").touch()
    git.add("data.txt")
    git.commit("initial")

    sha0 = git.get_sha()
    git.tag("mytag")

    # create sha1
    (path / "other.txt").touch()
    git.add("other.txt")
    git.commit("other")
    sha1 = git.get_sha()

    assert git.get_branch() == "main"
    assert git.get_tag() is None
    assert is_sha(sha1)
    assert git.get_revision() == "main"

    # create sha2
    (path / "end.txt").touch()
    git.add("end.txt")
    git.commit("end")
    sha2 = git.get_sha()

    # on tag
    git.checkout("mytag")

    assert git.get_branch() is None
    assert git.get_tag() == "mytag"
    assert git.get_sha() == sha0
    assert git.get_revision() == "mytag"

    # on sha0
    git.checkout(sha0)

    assert git.get_branch() is None
    assert git.get_tag() == "mytag"
    assert git.get_sha() == sha0
    assert git.get_revision() == "mytag"

    # on sha1
    git.checkout(sha1)

    assert git.get_branch() is None
    assert git.get_tag() is None
    assert git.get_sha() == sha1
    assert git.get_revision() == sha1

    # on another tag
    git.tag("myother", msg="other")

    assert git.get_branch() is None
    assert git.get_tag() == "myother"
    assert git.get_sha() == sha1
    assert git.get_revision() == "myother"

    # on branch
    git.checkout("main")
    assert git.get_branch() == "main"
    assert git.get_tag() is None
    assert git.get_sha() == sha2
    assert git.get_revision() == "main"
