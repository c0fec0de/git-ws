"""Command Line Interface."""
import logging
from pathlib import Path

import click
import coloredlogs  # type: ignore

from anyrepo import AnyRepo
from anyrepo._util import get_loglevel, resolve_relative
from anyrepo.const import MANIFEST_PATH_DEFAULT

from .info import info
from .manifest import manifest
from .options import groups_option, manifest_option, projects_option, update_option
from .util import Context, exceptionhandling, pass_context

_COLOR_INFO = "blue"


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx=None, verbose=0):
    """
    Multi Repository Management Tool.
    """
    level = get_loglevel(verbose)
    coloredlogs.install(level=level, fmt="%(name)s %(levelname)s %(message)s")
    ctx.obj = Context(verbose=verbose)


@main.command()
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@pass_context
def init(context, manifest, groups, update: bool = False):
    """
    Initialize AnyRepo workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.init(manifest_path=manifest, groups=groups, echo=click.secho)
        click.secho(f"Workspace initialized at {str(resolve_relative(arepo.path))!r}.")
        if update:
            arepo.update()
        else:
            click.secho(
                "Please continue with:\n\n    anyrepo update\n",
                fg=_COLOR_INFO,
            )


@main.command()
@click.argument("url")
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@pass_context
def clone(context, url, manifest, groups, update: bool = False):
    """
    Create a git clone, initialize AnyRepo workspace and create all dependent git clones.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.clone(url, manifest_path=manifest, groups=groups, echo=click.secho)
        if update:
            arepo.update()
        else:
            click.secho(
                f"Workspace initialized at {str(resolve_relative(arepo.path))!r}. "
                "Please continue with:\n\n    anyrepo update\n",
                fg=_COLOR_INFO,
            )


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.option("--rebase", is_flag=True, default=False, help="Run 'git rebase' instead of 'git pull'")
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
@pass_context
def update(context, projects, manifest, groups, rebase: bool = False, prune: bool = False):
    """Create/update all dependent git clones."""
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.update(project_paths=projects, manifest_path=manifest, groups=groups, rebase=rebase, prune=prune)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def git(context, projects, manifest, groups, command):
    """
    Run git command on projects.

    This command behaves identical to `anyrepo foreach -- git`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(("git",) + command, project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def fetch(context, projects, manifest, groups):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `anyrepo foreach -- git fetch`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(("git", "fetch"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def pull(context, projects, manifest, groups):
    """
    Run 'git pull' on projects.

    This command behaves identical to `anyrepo foreach -- git pull`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(("git", "pull"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def rebase(context, projects, manifest, groups):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `anyrepo foreach -- git rebase`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(("git", "rebase"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.option("-s", "--short", is_flag=True)
@pass_context
def status(context, projects, manifest, groups, short=False):
    """
    Run 'git status' on projects.

    This command behaves identical to `anyrepo foreach -- git status`.
    """
    cmd = ["git", "status"]
    if short:
        cmd.append("-s")
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(cmd, project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def diff(context, projects, manifest, groups):
    """
    Run 'git diff' on projects.

    This command behaves identical to `anyrepo foreach -- git diff`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(("git", "diff"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def foreach(context, projects, manifest, groups, command):
    """
    Run 'command' on projects.

    Please use '--' to separate anyrepo command line options from options forwarded to the `command`
    (i.e. `anyrepo foreach -- ls -l`)
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest, echo=click.secho)
        arepo.foreach(command, project_paths=projects, groups=groups)


@main.command()
@click.option(
    "--project",
    "-P",
    type=click.Path(file_okay=False),
    help="Project Path. Current working directory by default.",
)
@manifest_option(initial=True)
@pass_context
def create_manifest(context, project, manifest):
    """Create Manifest."""
    with exceptionhandling(context):
        path = AnyRepo.create_manifest(project, manifest)
        click.secho(f"Manifest {str(path)!r} created.", fg=_COLOR_INFO)


main.add_command(manifest)
main.add_command(info)
