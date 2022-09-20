"""Manifest Testing."""
from pytest import raises

from anyrepo.manifest import Defaults, Manifest, Project, Remote


def test_remote():
    """Test Remotes."""
    remote = Remote(name="origin")
    assert remote.name == "origin"
    assert remote.urlbase is None

    remote = Remote(name="origin2", urlbase="base")
    assert remote.name == "origin2"
    assert remote.urlbase == "base"


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
    assert project.suburl is None
    assert project.url is None
    assert project.revision is None
    assert project.path is None
    assert project.manifest is None

    with raises(ValueError):
        Project(name="name", remote="remote", url="url")
    with raises(ValueError):
        Project(name="name", suburl="suburl", url="url")
    with raises(ValueError):
        Project(name="name", suburl="suburl")


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
            {"name": "remote2", "urlbase": "https://git.example.com/base2"},
            {"name": "remote1", "urlbase": "https://git.example.com/base1"},
        ],
        "projects": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "suburl": "sub.git", "revision": "main"},
        ],
    }
    manifest = Manifest(**data)
    assert manifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest.remotes == [
        Remote(name="remote2", urlbase="https://git.example.com/base2"),
        Remote(name="remote1", urlbase="https://git.example.com/base1"),
    ]
    assert manifest.projects == [
        Project(name="dep1", remote="remote1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        Project(name="dep3", remote="remote1", suburl="sub.git", revision="main"),
    ]

    # resolved
    rmanifest = manifest.resolve()
    assert rmanifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert rmanifest.remotes == [
        Remote(name="remote2", urlbase="https://git.example.com/base2"),
        Remote(name="remote1", urlbase="https://git.example.com/base1"),
    ]
    assert rmanifest.projects == [
        Project(name="dep1", url="https://git.example.com/base1/dep1", revision="v1.3", path="dep1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", revision="v1.3", path="dep2dir"),
        Project(name="dep3", url="https://git.example.com/base1/sub.git", revision="main", path="dep3"),
    ]

    with raises(ValueError):
        Manifest(
            projects=[
                {"name": "dep1", "remote": "remote1"},
                {"name": "dep2", "url": "https://git.example.com/base3/dep2.git"},
            ]
        ).resolve()
