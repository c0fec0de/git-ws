"""Manifest Testing."""
from pytest import raises

from anyrepo.manifest import Defaults, Manifest, ManifestSpec, Project, ProjectSpec, Remote


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


def test_project_spec():
    """Test ProjectSpec."""
    project_spec = ProjectSpec(name="name")
    assert project_spec.name == "name"
    assert project_spec.remote is None
    assert project_spec.sub_url is None
    assert project_spec.url is None
    assert project_spec.revision is None

    with raises(ValueError):
        ProjectSpec(name="name", remote="remote", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url", url="url")
    with raises(ValueError):
        ProjectSpec(name="name", sub_url="sub-url")


def test_manifest_spec(tmp_path):
    """Test ManifestSpec."""
    manifest = ManifestSpec()
    assert manifest.defaults == Defaults()
    assert not manifest.remotes
    assert not manifest.dependencies

    filepath = tmp_path / "manifest.toml"
    manifest.save(filepath)
    assert filepath.read_text().split("\n") == [""]


def test_manifest_spec_from_data(tmp_path):
    """Determine ManifestSpec from Data."""
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
    manifest = ManifestSpec(**data)
    assert manifest.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest.remotes == [
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    ]
    assert manifest.dependencies == [
        ProjectSpec(name="dep1", remote="remote1"),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
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
    assert ManifestSpec.load(filepath) == manifest

    rdependencies = [
        Project.from_spec(manifest.defaults, manifest.remotes, project) for project in manifest.dependencies
    ]
    assert rdependencies == [
        Project(name="dep1", url="https://git.example.com/base1/dep1", revision="v1.3", path="dep1"),
        Project(name="dep2", url="https://git.example.com/base3/dep2.git", revision="v1.3", path="dep2dir"),
        Project(name="dep3", url="https://git.example.com/base1/sub.git", revision="main", path="dep3"),
    ]


def test_manifest_spec_from_other_data(tmp_path):
    """Determine ManifestSpec from Other Data."""
    data = {
        "defaults": {
            "remote": "remote1",
        },
        "dependencies": [
            {"name": "dep1", "remote": "remote1"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest = ManifestSpec(**data)
    assert manifest.defaults == Defaults(remote="remote1")
    assert not manifest.remotes
    assert manifest.dependencies == [
        ProjectSpec(name="dep1", remote="remote1"),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    ]


def test_manifest_spec_not_remote():
    """Determine ManifestSpec from Other Data."""
    remotes = [Remote(name="remote2", url_base="foo")]
    defaults = Defaults()
    project = Project.from_spec(defaults=defaults, remotes=remotes, spec=ProjectSpec(name="foo"))
    assert project.name == "foo"
    assert project.url is None


def test_manifest_spec_missing_remote():
    """Determine ManifestSpec with missing Remote."""
    remotes = [Remote(name="remote2", url_base="foo")]
    defaults = Defaults()
    with raises(ValueError) as exc:
        Project.from_spec(defaults=defaults, remotes=remotes, spec=ProjectSpec(name="foo", remote="remote1"))
        assert str(exc) == "ValueError: Unknown remote remote1 for project foo"


def test_manifest():
    """Test Manifest."""
    data = {
        "remotes": [
            {
                "name": "remote1",
                "url-base": "url1",
            },
            {
                "name": "remote2",
                "url-base": "url2",
            },
        ],
        "defaults": {
            "remote": "remote1",
        },
        "dependencies": [
            {"name": "dep1", "remote": "remote2"},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    manifest = Manifest.from_spec(manifest_spec)
    assert manifest.dependencies == [
        Project(name="dep1", path="dep1", url="url2/dep1"),
        Project(name="dep2", path="dep2dir", url="https://git.example.com/base3/dep2.git"),
        Project(name="dep3", path="dep3", url="url1/sub.git", revision="main"),
    ]
    assert manifest.path is None
