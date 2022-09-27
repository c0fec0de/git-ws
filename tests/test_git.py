"""Git Testing."""
from anyrepo._git import Git


def test_git(tmp_path):
    """GIT testing."""
    git = Git(tmp_path)
    assert not git.is_cloned()
    git.init()
    assert git.is_cloned()
    assert git.get_url() is None

    git.set_config("user.email", "you@example.com")
    git.set_config("user.name", "you")

    (tmp_path / "data.txt").touch()
    git.add("data.txt")
    git.commit("initial")
