"""Command Line Interface."""
import logging

import click
import coloredlogs  # type: ignore

from anyrepo import AnyRepo
from anyrepo._util import get_loglevel

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


def _projects():
    return click.option(
        "--project",
        "-P",
        "projects",
        multiple=True,
        help="Project path to operate on only. All by default. This option can be specified multiple times.",
    )


@click.command()
@_projects()
def init(projects):
    """
    Initialize AnyRepo workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling():
        arepo = AnyRepo.init()
        arepo.update(projects)


@click.command()
@click.argument("url")
@_projects()
def clone(url, projects):
    """
    Create a git clone, initialize AnyRepo workspace and create all dependent git clones.
    """
    with exceptionhandling():
        arepo = AnyRepo.clone(url)
        arepo.update(projects)


@click.command()
@_projects()
def update(projects):
    """Create/update all dependent git clones."""
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.update(projects, banner=banner)


@click.command()
@_projects()
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
@_projects()
def fetch(projects):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `anyrepo foreach git fetch`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "fetch"), project_paths=projects, banner=banner)


@click.command()
@_projects()
def pull(projects):
    """
    Run 'git pull' on projects.

    This command behaves identical to `anyrepo foreach git pull`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "pull"), project_paths=projects, banner=banner)


@click.command()
@_projects()
def rebase(projects):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `anyrepo foreach git rebase`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "rebase"), project_paths=projects, banner=banner)


@click.command()
@_projects()
def status(projects):
    """
    Run 'git status' on projects.

    This command behaves identical to `anyrepo foreach git status`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "status"), project_paths=projects, banner=banner)


@click.command()
@_projects()
def diff(projects):
    """
    Run 'git diff' on projects.

    This command behaves identical to `anyrepo foreach git diff`.
    """
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(("git", "diff"), project_paths=projects, banner=banner)


@click.command()
@_projects()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def foreach(projects, command):
    """Run 'command' on projects."""
    with exceptionhandling():
        arepo = AnyRepo.from_path()
        arepo.foreach(command, project_paths=projects, banner=banner)


main.add_command(init)
main.add_command(clone)
main.add_command(update)
main.add_command(git)
main.add_command(fetch)
main.add_command(pull)
main.add_command(rebase)
main.add_command(status)
main.add_command(foreach)
main.add_command(manifest)
