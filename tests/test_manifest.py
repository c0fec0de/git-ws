"""Manifest Testing."""
from pytest import raises

from anyrepo.manifest import Defaults, Manifest, Project, Remote, ResolvedProject


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
    assert manifest.path is None
    assert manifest.defaults == Defaults()
    assert not manifest.remotes
    assert not manifest.dependencies


def test_manifest_from_data(tmp_path):
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
        "dependencies": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest = Manifest(**data)
    assert manifest.path is None
    assert manifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest.remotes == [
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    ]
    assert manifest.dependencies == [
        Project(name="dep1", remote="remote1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        Project(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    ]

    filepath = tmp_path / "manifest.toml"
    manifest.save(filepath)
    assert filepath.read_text().split("\n") == [
        "[defaults]",
        'remote = "remote1"',
        'revision = "v1.3"',
        "",
        "[[remotes]]",
        'name = "remote2"',
        'url-base = "https://git.example.com/base2"',
        "",
        "[[remotes]]",
        'name = "remote1"',
        'url-base = "https://git.example.com/base1"',
        "",
        "[[dependencies]]",
        'name = "dep1"',
        'remote = "remote1"',
        "",
        "[[dependencies]]",
        'name = "dep2"',
        'url = "https://git.example.com/base3/dep2.git"',
        'path = "dep2dir"',
        "",
        "[[dependencies]]",
        'name = "dep3"',
        'remote = "remote1"',
        'sub-url = "sub.git"',
        'revision = "main"',
        "",
    ]
    assert Manifest.load(filepath) == manifest

    rdependencies = [
        ResolvedProject.from_project(manifest.defaults, manifest.remotes, project) for project in manifest.dependencies
    ]
    assert rdependencies == [
        ResolvedProject(name="dep1", url="https://git.example.com/base1/dep1", revision="v1.3", path="dep1"),
        ResolvedProject(name="dep2", url="https://git.example.com/base3/dep2.git", revision="v1.3", path="dep2dir"),
        ResolvedProject(name="dep3", url="https://git.example.com/base1/sub.git", revision="main", path="dep3"),
    ]


def test_manifest_from_other_data(tmp_path):
    """Determine Manifest from Other Data."""
    data = {
        "path": "root",
        "defaults": {
            "remote": "remote1",
        },
        "dependencies": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest = Manifest(**data)
    assert manifest.path == "root"
    assert manifest.defaults == Defaults(remote="remote1")
    assert not manifest.remotes
    assert manifest.dependencies == [
        Project(name="dep1", remote="remote1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        Project(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    ]
