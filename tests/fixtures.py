"""Fixtures."""
from contextlib import contextmanager

from pytest import fixture

from anyrepo.manifest import Manifest, ProjectSpec

from .util import chdir, run


@contextmanager
def git_repo(path, commit=None):
    """Initialize Repo."""
    path.mkdir(parents=True, exist_ok=True)
    with chdir(path):
        run(("git", "init", "-b", "main"), check=True)
        run(("git", "config", "user.email", "you@example.com"), check=True)
        run(("git", "config", "user.name", "you"), check=True)
        yield path
        if commit:
            run(("git", "add", "-A"), check=True)
            run(("git", "commit", "-m", commit), check=True)


@fixture
def repos(tmp_path):
    """Fixture with main and four depedency repos."""

    repos_path = tmp_path / "repos"

    with git_repo(repos_path / "main", commit="initial") as path:
        (path / "data.txt").write_text("main")
        Manifest(
            dependencies=[
                ProjectSpec(name="dep1", url="../dep1"),
                ProjectSpec(name="dep2", url="../dep2"),
            ]
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep1", commit="initial") as path:
        (path / "data.txt").write_text("dep1")
        Manifest(
            dependencies=[
                ProjectSpec(name="dep4", url="../dep4"),
            ]
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep2", commit="initial") as path:
        (path / "data.txt").write_text("dep2")
        Manifest(
            dependencies=[
                ProjectSpec(name="dep3", url="../dep3"),
            ]
        ).save(path / "anyrepo.toml")

    with git_repo(repos_path / "dep3", commit="initial") as path:
        (path / "data.txt").write_text("dep3")

    with git_repo(repos_path / "dep4", commit="initial") as path:
        (path / "data.txt").write_text("dep4")

    with git_repo(repos_path / "dep5", commit="initial") as path:
        (path / "data.txt").write_text("dep5")

    yield repos_path
