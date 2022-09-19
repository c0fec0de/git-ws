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


def test_manifest():
    """Test Manifest."""
    manifest = Manifest()
    assert manifest.defaults == Defaults()
    assert manifest.remotes == []


def test_manifest_from_data():
    """Determine Manifest from Data."""
    data = {
        "defaults": {
            "remote": "remote1",
            "revision": "v1.3",
        },
        "remotes": [
            {"name": "remote1", "urlbase": "https://git.example.com/base1"},
            {"name": "remote2", "urlbase": "https://git.example.com/base2"},
        ],
        "projects": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
        ],
    }
    manifest = Manifest(**data)
    assert manifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest.remotes == [
        Remote(name="remote1", urlbase="https://git.example.com/base1"),
        Remote(name="remote2", urlbase="https://git.example.com/base2"),
    ]
    projects = [
        Project(name="dep1", remote="remote1", url=None, revision=None, path=None, manifest=None),
        Project(
            name="dep2",
            remote=None,
            url="https://git.example.com/base3/dep2.git",
            revision=None,
            path="dep2dir",
            manifest=None,
        ),
    ]
    assert manifest.projects == projects
