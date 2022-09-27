"""Command Line Interface."""
import logging
from pathlib import Path

import click
import coloredlogs  # type: ignore

from anyrepo import AnyRepo
from anyrepo._util import get_loglevel, resolve_relative
from anyrepo.const import MANIFEST_PATH_DEFAULT

from .manifest import manifest
from .util import Context, exceptionhandling, pass_context

_COLOR_INFO = "blue"


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx=None, verbose=0):
    """
    Multi Repository Management Tool.
    """
    level = get_loglevel(verbose)
    coloredlogs.install(level=level, fmt="%(name)s %(levelname)s %(message)s")
    ctx.obj = Context(verbose=verbose)


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


@main.command()
@_manifest_option()
@pass_context
def init(context, manifest: Path = MANIFEST_PATH_DEFAULT):
    """
    Initialize AnyRepo workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.init(manifest_path=manifest, colorprint=click.secho)
        click.secho(
            f"Workspace initialized at '{resolve_relative(arepo.path)!s}'. "
            "Please continue with:\n\n    anyrepo update\n",
            fg=_COLOR_INFO,
        )


@main.command()
@click.argument("url")
@_manifest_option()
@pass_context
def clone(context, url, manifest: Path = MANIFEST_PATH_DEFAULT):
    """
    Create a git clone, initialize AnyRepo workspace and create all dependent git clones.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.clone(url, manifest_path=manifest, colorprint=click.secho)
        click.secho(
            f"Workspace initialized at '{resolve_relative(arepo.path)!s}'. "
            "Please continue with:\n\n    anyrepo update\n",
            fg=_COLOR_INFO,
        )


@main.command()
@_projects_option()
@_manifest_option()
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
@pass_context
def update(context, projects, manifest: Path = MANIFEST_PATH_DEFAULT, prune: bool = False):
    """Create/update all dependent git clones."""
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.update(projects, manifest_path=manifest, prune=prune)


@main.command()
@_projects_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def git(context, projects, command):
    """
    Run git command on projects.

    This command behaves identical to `anyrepo foreach git`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git",) + command, project_paths=projects)


@main.command()
@_projects_option()
@pass_context
def fetch(context, projects):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `anyrepo foreach git fetch`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git", "fetch"), project_paths=projects)


@main.command()
@_projects_option()
@pass_context
def pull(context, projects):
    """
    Run 'git pull' on projects.

    This command behaves identical to `anyrepo foreach git pull`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git", "pull"), project_paths=projects)


@main.command()
@_projects_option()
@pass_context
def rebase(context, projects):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `anyrepo foreach git rebase`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git", "rebase"), project_paths=projects)


@main.command()
@_projects_option()
@pass_context
def status(context, projects):
    """
    Run 'git status' on projects.

    This command behaves identical to `anyrepo foreach git status`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git", "status"), project_paths=projects)


@main.command()
@_projects_option()
@pass_context
def diff(context, projects):
    """
    Run 'git diff' on projects.

    This command behaves identical to `anyrepo foreach git diff`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(("git", "diff"), project_paths=projects)


@main.command()
@_projects_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def foreach(context, projects, command):
    """Run 'command' on projects."""
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(colorprint=click.secho)
        arepo.foreach(command, project_paths=projects)


@main.command()
@click.option(
    "--project",
    "-P",
    type=click.Path(file_okay=False),
    help="Project Path. Current working directory by default.",
)
@_manifest_option()
@pass_context
def create_manifest(context, project, manifest):
    """Create Manifest."""
    with exceptionhandling(context):
        path = AnyRepo.create_manifest(project, manifest)
        click.secho(f"Manifest {path!s} created.", fg=_COLOR_INFO)


main.add_command(manifest)
