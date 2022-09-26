"""Command Line Interface."""
import logging
from pathlib import Path

import click
import coloredlogs  # type: ignore

from anyrepo import AnyRepo
from anyrepo._util import get_loglevel, resolve_relative
from anyrepo.const import MANIFEST_PATH_DEFAULT

from .manifest import manifest
from .util import banner, exceptionhandling


@click.group()
@click.option("-v", "--verbose", count=True)
def main(verbose=None):
    """
    Multi Repository Management Tool.
    """
    level = get_loglevel(verbose)
    coloredlogs.install(level=level, fmt="%(name)s %(levelname)s %(message)s")


def _projects_option():
    return click.option(
        "--project",
        "-P",
        "projects",
        multiple=True,
        help="Project path to operate on only. All by default. This option can be specified multiple times.",
    )


def _manifest_option():
    return click.option(
        "--manifest",
        "-M",
        type=click.Path(dir_okay=False),
        default=MANIFEST_PATH_DEFAULT,
        help=f"Manifest file. '{MANIFEST_PATH_DEFAULT!s}' by default.",
    )


@click.command()
@_projects_option()
@_manifest_option()
def init(projects, manifest: Path = MANIFEST_PATH_DEFAULT):
    """
    Initialize AnyRepo workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling():
        arepo = AnyRepo.init(manifest_path=manifest)
        click.echo(f"Workspace initialized at {resolve_relative(arepo.path)!s}")
        arepo.update(projects, manifest_path=manifest, banner=banner)


@click.command()
@click.argument("url")
@_projects_option()
@_manifest_option()
def clone(url, projects, manifest: Path = MANIFEST_PATH_DEFAULT):
    """
    Create a git clone, initialize AnyRepo workspace and create all dependent git clones.
    """
    with exceptionhandling():
        arepo = AnyRepo.clone(url, manifest_path=manifest)
        arepo.update(projects, manifest_path=manifest, banner=banner)


@click.command()
@_projects_option()
@_manifest_option()
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
def update(projects, manifest: Path = MANIFEST_PATH_DEFAULT, prune: bool = False):
    """Create/update all dependent git clones."""
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.update(projects, manifest_path=manifest, prune=prune, banner=banner)


@click.command()
@_projects_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def git(projects, command):
    """
    Run git command on projects.

    This command behaves identical to `anyrepo foreach git`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git",) + command, project_paths=projects, banner=banner)


@click.command()
@_projects_option()
def fetch(projects):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `anyrepo foreach git fetch`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "fetch"), project_paths=projects, banner=banner)


@click.command()
@_projects_option()
def pull(projects):
    """
    Run 'git pull' on projects.

    This command behaves identical to `anyrepo foreach git pull`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "pull"), project_paths=projects, banner=banner)


@click.command()
@_projects_option()
def rebase(projects):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `anyrepo foreach git rebase`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "rebase"), project_paths=projects, banner=banner)


@click.command()
@_projects_option()
def status(projects):
    """
    Run 'git status' on projects.

    This command behaves identical to `anyrepo foreach git status`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "status"), project_paths=projects, banner=banner)


@click.command()
@_projects_option()
def diff(projects):
    """
    Run 'git diff' on projects.

    This command behaves identical to `anyrepo foreach git diff`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "diff"), project_paths=projects, banner=banner)


@click.command()
@_projects_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def foreach(projects, command):
    """Run 'command' on projects."""
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(command, project_paths=projects, banner=banner)


@click.command()
@click.option(
    "--project",
    "-P",
    type=click.Path(file_okay=False),
    help="Project Path. Current working directory by default.",
)
@_manifest_option()
def create_manifest(project, manifest):
    """Create Manifest."""
    with exceptionhandling():
        path = AnyRepo.create_manifest(project, manifest)
        click.echo(f"Manifest {path!s} created.")


main.add_command(clone)
main.add_command(fetch)
main.add_command(foreach)
main.add_command(git)
main.add_command(init)
main.add_command(manifest)
main.add_command(pull)
main.add_command(rebase)
main.add_command(status)
main.add_command(update)
main.add_command(create_manifest)
