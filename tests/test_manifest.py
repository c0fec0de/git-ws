"""Manifest Testing."""
from pytest import raises

from anyrepo.manifest import Defaults, Manifest, Project, Remote


def test_remote():
    """Test Remotes."""
    remote = Remote(name="origin")
    assert remote.name == "origin"
    assert remote.url_base is None

    remote = Remote(name="origin2", url_base="base")
    assert remote.name == "origin2"
    assert remote.url_base == "base"


def test_defaults():
    """Test Defaults."""
    defaults = Defaults()
    assert defaults.remote is None
    assert defaults.revision is None

    defaults = Defaults(remote="remote")
    assert defaults.remote == "remote"
    assert defaults.revision is None

    defaults = Defaults(revision="Revision")
    assert defaults.remote is None
    assert defaults.revision == "Revision"


def test_project():
    """Test Project."""
    project = Project(name="name")
    assert project.name == "name"
    assert project.remote is None
    assert project.sub_url is None
    assert project.url is None
    assert project.revision is None
    assert project.path is None

    with raises(ValueError):
        Project(name="name", remote="remote", url="url")
    with raises(ValueError):
        Project(name="name", sub_url="sub-url", url="url")
    with raises(ValueError):
        Project(name="name", sub_url="sub-url")


def test_manifest():
    """Test Manifest."""
    manifest = Manifest()
    assert manifest.defaults == Defaults()
    assert not manifest.remotes


def test_manifest_from_data():
    """Determine Manifest from Data."""
    data = {
        "defaults": {
            "remote": "remote1",
            "revision": "v1.3",
        },
        "remotes": [
            {"name": "remote2", "url-base": "https://git.example.com/base2"},
            {"name": "remote1", "url-base": "https://git.example.com/base1"},
        ],
        "projects": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest = Manifest(**data)
    assert manifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest.remotes == [
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    ]
    assert manifest.projects == [
        Project(name="dep1", remote="remote1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        Project(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    ]
