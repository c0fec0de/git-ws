"""Manifest Testing."""
from pytest import raises

from anyrepo.datamodel import Defaults, Group, Manifest, ManifestSpec, Project, ProjectSpec, Remote


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


def test_project_group():
    """Group."""
    group = Group(name="name")
    assert group.name == "name"
    assert group.optional

    group = Group(name="name", optional=False)
    assert group.name == "name"
    assert not group.optional


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
    manifest_spec = ManifestSpec()
    assert manifest_spec.defaults == Defaults()
    assert not manifest_spec.remotes
    assert not manifest_spec.dependencies

    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
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
        "groups": [
            {"name": "foo", "optional": False},
            {"name": "bar"},
        ],
        "dependencies": [
            {"name": "dep1", "remote": "remote1", "groups": ["test", "foo"]},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main"},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    assert manifest_spec.defaults == Defaults(remote="remote1", revision="v1.3")
    assert manifest_spec.remotes == (
        Remote(name="remote2", url_base="https://git.example.com/base2"),
        Remote(name="remote1", url_base="https://git.example.com/base1"),
    )
    assert manifest_spec.groups == (Group(name="foo", optional=False), Group(name="bar"))
    assert manifest_spec.dependencies == (
        ProjectSpec(name="dep1", remote="remote1", groups=("test", "foo")),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    )

    filepath = tmp_path / "manifest.toml"
    manifest_spec.save(filepath)
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
        "[[groups]]",
        'name = "foo"',
        "optional = false",
        "",
        "[[groups]]",
        'name = "bar"',
        "",
        "[[dependencies]]",
        'name = "dep1"',
        'remote = "remote1"',
        'groups = ["test", "foo"]',
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
    assert ManifestSpec.load(filepath) == manifest_spec

    rdependencies = [Project.from_spec(manifest_spec, project) for project in manifest_spec.dependencies]
    assert rdependencies == [
        Project(
            name="dep1",
            url="https://git.example.com/base1/dep1",
            revision="v1.3",
            path="dep1",
            groups=(Group(name="test"), Group(name="foo", optional=False)),
        ),
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
    assert manifest.dependencies == (
        ProjectSpec(name="dep1", remote="remote1"),
        ProjectSpec(name="dep2", url="https://git.example.com/base3/dep2.git", path="dep2dir"),
        ProjectSpec(name="dep3", remote="remote1", sub_url="sub.git", revision="main"),
    )


def test_manifest_spec_not_remote():
    """Determine ManifestSpec from Other Data."""
    remotes = (Remote(name="remote2", url_base="foo"),)
    manifest_spec = ManifestSpec(remotes=remotes)
    project = Project.from_spec(manifest_spec, spec=ProjectSpec(name="foo"))
    assert project.name == "foo"
    assert project.url is None


def test_manifest_spec_missing_remote():
    """Determine ManifestSpec with missing Remote."""
    remotes = (Remote(name="remote2", url_base="foo"),)
    manifest_spec = ManifestSpec(remotes=remotes)
    with raises(ValueError) as exc:
        Project.from_spec(manifest_spec, spec=ProjectSpec(name="foo", remote="remote1"))
    assert str(exc.value) == "Unknown remote remote1 for project foo"


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
        "groups": [
            {"name": "doc", "optional": True},
            {"name": "bar"},
        ],
        "dependencies": [
            {"name": "dep1", "remote": "remote2", "groups": ["test", "doc"]},
            {"name": "dep2", "path": "dep2dir", "url": "https://git.example.com/base3/dep2.git"},
            {"name": "dep3", "remote": "remote1", "sub-url": "sub.git", "revision": "main", "groups": ["test"]},
        ],
    }
    manifest_spec = ManifestSpec(**data)
    manifest = Manifest.from_spec(manifest_spec)
    assert manifest.dependencies == (
        Project(
            name="dep1", path="dep1", url="url2/dep1", groups=(Group(name="test"), Group(name="doc", optional=True))
        ),
        Project(name="dep2", path="dep2dir", url="https://git.example.com/base3/dep2.git"),
        Project(name="dep3", path="dep3", url="url1/sub.git", revision="main", groups=(Group(name="test"),)),
    )
    assert manifest.path is None
