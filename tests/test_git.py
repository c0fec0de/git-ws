# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Git Testing."""
import re

from pytest import fixture

from gitws.git import Git

# pylint: disable=unused-import
from .fixtures import repos


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
    git.add(("data.txt",))
    git.commit("initial")


def test_git_revisions(git):
    """Git Versioning."""
    # on branch, sha0
    path = git.path

    (path / "data.txt").touch()

    git.add(("data.txt",))

    git.commit("initial")

    sha0 = git.get_sha()
    git.tag("mytag")

    # create sha1
    (path / "other.txt").touch()
    git.add(("other.txt",))
    git.commit("other")
    sha1 = git.get_sha()

    assert git.get_branch() == "main"
    assert git.get_tag() is None
    assert is_sha(sha1)
    assert git.get_revision() == "main"

    # create sha2
    (path / "end.txt").touch()
    git.add(("end.txt",))
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


def test_git_status(git):
    """Git Status."""
    path = git.path

    assert [str(item) for item in git.status()] == []

    (path / "data.txt").touch()
    (path / "other.txt").touch()

    assert [str(item) for item in git.status()] == ["?? data.txt", "?? other.txt"]

    git.add(("data.txt",))

    assert [str(item) for item in git.status()] == ["A  data.txt", "?? other.txt"]

    (path / "data.txt").unlink()

    assert [str(item) for item in git.status()] == ["AD data.txt", "?? other.txt"]

    git.commit("initial")

    assert [str(item) for item in git.status()] == [" D data.txt", "?? other.txt"]

    (path / "data.txt").touch()

    assert [str(item) for item in git.status()] == ["?? other.txt"]

    (path / "other.txt").unlink()

    assert [str(item) for item in git.status()] == []


def test_git_has_changes(tmp_path, repos):
    """Git Has Changes."""

    main = tmp_path / "main"
    git = Git(main)
    git.clone(str(repos / "main"))

    path = git.path

    assert not git.has_work_changes()
    assert not git.has_index_changes()
    assert not git.has_changes()
    assert git.is_empty()

    (path / "new.txt").touch()

    assert not git.has_work_changes()
    assert not git.has_index_changes()
    assert not git.has_changes()
    assert not git.is_empty()

    git.add(("new.txt",))

    assert not git.has_work_changes()
    assert git.has_index_changes()
    assert git.has_changes()
    assert not git.is_empty()

    (path / "new.txt").unlink()

    assert git.has_work_changes()
    assert git.has_index_changes()
    assert git.has_changes()
    assert not git.is_empty()

    git.commit("initial")

    assert git.has_work_changes()
    assert not git.has_index_changes()
    assert git.has_changes()
    assert not git.is_empty()

    (path / "new.txt").touch()

    assert not git.has_work_changes()
    assert not git.has_index_changes()
    assert not git.has_changes()
    assert not git.is_empty()


def test_git_empty(git):
    """Git Has Changes."""
    path = git.path

    assert git.is_empty()

    (path / "new.txt").touch()

    assert not git.is_empty()

    git.add(("new.txt",))

    assert not git.is_empty()

    (path / "new.txt").unlink()

    assert not git.is_empty()

    git.commit("initial")

    assert not git.is_empty()

    (path / "new.txt").touch()

    assert not git.is_empty()
