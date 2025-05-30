# Copyright 2022-2025 c0fec0de
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
from pathlib import Path

from pytest import fixture

from gitws._util import run
from gitws.git import Git

from .fixtures import git_repo
from .util import path2url


def is_sha(sha):
    """Return if result is a SHA."""
    return re.match(r"^[0-9a-fA-F]+$", sha) is not None


@fixture
def git(tmp_path) -> Git:
    """Testfixture with initialized GIT repo."""
    path = tmp_path / "git"
    path.mkdir()
    git = Git(path)
    assert not git.is_cloned()
    run(("git", "init"), cwd=path)
    run(("git", "checkout", "-b", "main"), cwd=path)
    git.set_config("user.email", "you@example.com")
    git.set_config("user.name", "you")

    (path / "file.txt").touch()
    git.add((Path("file.txt"),))
    git.commit("file")
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

    assert git.get_tags() == ()

    sha0 = git.get_sha()
    git.tag("mytag")

    # create sha1
    (path / "other.txt").touch()
    git.add(("other.txt",))
    git.commit("other")
    sha1 = git.get_sha()

    assert git.get_branch() == "main"
    assert git.get_tag() is None
    assert git.get_tags() == ("mytag",)
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
    assert git.get_tags() == ("mytag",)
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

    assert git.diff() is None

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
    git.clone(path2url(repos / "main"))
    git.set_config("user.email", "you@example.com")
    git.set_config("user.name", "you")

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


def test_git_empty_stash(tmp_path, git):
    """Empty Stash."""
    clone_path = tmp_path / "clone"
    clone_path.mkdir()
    clone = Git(clone_path)
    clone.clone(str(git.path))

    assert clone.is_empty()

    (clone_path / "foo.txt").touch()
    run(("git", "stash", "-u"), cwd=clone_path)

    assert not clone.is_empty()


def test_cache_modified(tmp_path, repos):
    """Broken cache."""
    cache_path = tmp_path / "cache"
    repo = (repos / "dep2").resolve()

    # first clone - initialize cache
    git = Git(tmp_path / "main1", clone_cache=cache_path)
    git.clone(str(repo))
    git.checkout("1-feature")
    assert (git.path / "data.txt").read_text() == "dep2-feature"

    # corrupt cache
    cache_entry_path = next(iter(cache_path.glob("*")))
    (cache_entry_path / "data.txt").write_text("dep2-feature*")
    (cache_entry_path / "new.txt").touch()

    # second clone on corrupt cache
    git = Git(tmp_path / "main2", clone_cache=cache_path)
    git.clone(str(repo))
    git.checkout("1-feature")
    assert (git.path / "data.txt").read_text() == "dep2-feature"
    assert not (git.path / "new.txt").exists()


def test_empty(tmp_path):
    """Test is_empty()."""
    Git.init(tmp_path)
    git = Git(tmp_path)
    assert git.is_empty()
    assert tuple(git.diffstat()) == ()


def test_cache_nomain(tmp_path):
    """No Main."""
    repos_path = tmp_path / "repos"

    # Init Repo
    with git_repo(repos_path / "main", commit="initial", branch="devel") as path:
        (path / "data.txt").write_text("main")
    cache_path = tmp_path / "cache"

    # First Clone
    git = Git(tmp_path / "main1", clone_cache=cache_path)
    git.clone(path2url(repos_path / "main"))
    assert (git.path / "data.txt").read_text() == "main"

    cache_entry_path = next(cache_path.glob("*"))
    marker_filepath = cache_entry_path / ".git" / ".marker"
    marker_filepath.touch()
    assert marker_filepath.exists()

    # Second Clone
    git = Git(tmp_path / "main2", clone_cache=cache_path)
    git.clone(path2url(repos_path / "main"))
    assert (git.path / "data.txt").read_text() == "main"

    assert marker_filepath.exists()
