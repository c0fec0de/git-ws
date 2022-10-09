"""Command Line Interface."""
import logging
from pathlib import Path

import click
import coloredlogs  # type: ignore

from anyrepo import AnyRepo, AppConfig
from anyrepo._util import resolve_relative
from anyrepo.const import MANIFEST_PATH_DEFAULT

from .common import COLOR_INFO, Context, Error, exceptionhandling, get_loglevel, pass_context
from .info import info
from .manifest import manifest
from .options import force_option, groups_option, manifest_option, paths_argument, projects_option, update_option

_LOGGING_FORMAT = "%(name)s %(levelname)s %(message)s"


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True)
@click.version_option()
@click.pass_context
def main(ctx=None, verbose=0):
    """
    Multi Repository Management Tool.
    """
    app_config = AppConfig()
    level = get_loglevel(verbose)
    color = Error.color = app_config.options.color_ui
    if color:
        coloredlogs.install(level=level, fmt=_LOGGING_FORMAT)
    else:
        logging.basicConfig(level=level, format=_LOGGING_FORMAT)
    ctx.obj = Context(verbose=verbose, color=color)


@main.command()
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@pass_context
def init(context, manifest_path=None, groups=None, update: bool = False):
    """
    Initialize AnyRepo workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.init(manifest_path=manifest_path, groups=groups, echo=context.echo)
        click.secho(f"Workspace initialized at {str(resolve_relative(arepo.path))!r}.")
        if update:
            arepo.update(skip_main=True)
        else:
            click.secho(
                "Please continue with:\n\n    anyrepo update\n",
                fg=COLOR_INFO,
            )


@main.command()
@pass_context
def deinit(context):
    """
    Deinitialize AnyRepo workspace.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(echo=context.echo)
        arepo.deinit()
        click.secho(f"Workspace deinitialized at {str(resolve_relative(arepo.path))!r}.")


@main.command()
@click.argument("url")
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@pass_context
def clone(context, url, manifest_path=None, groups=None, update: bool = False):
    """
    Create a git clone, initialize AnyRepo workspace and create all dependent git clones.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.clone(url, manifest_path=manifest_path, groups=groups, echo=context.echo)
        if update:
            arepo.update(skip_main=True)
        else:
            click.secho(
                f"Workspace initialized at {str(resolve_relative(arepo.path))!r}. "
                "Please continue with:\n\n    anyrepo update\n",
                fg=COLOR_INFO,
            )


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.option("--skip-main", "-S", is_flag=True, default=False, help="Skip Main Repository")
@click.option("--rebase", is_flag=True, default=False, help="Run 'git rebase' instead of 'git pull'")
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
@force_option()
@pass_context
def update(
    context,
    projects=None,
    manifest_path=None,
    groups=None,
    skip_main: bool = False,
    rebase: bool = False,
    prune: bool = False,
    force: bool = False,
):
    """Create/update all dependent git clones."""
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.update(
            project_paths=projects,
            manifest_path=manifest_path,
            groups=groups,
            skip_main=skip_main,
            rebase=rebase,
            prune=prune,
            force=force,
        )


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def git(context, command, projects=None, manifest_path=None, groups=None):
    """
    Run git command on projects.

    This command behaves identical to `anyrepo foreach -- git`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git",) + command, project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def fetch(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `anyrepo foreach -- git fetch`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "fetch"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def pull(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git pull' on projects.

    This command behaves identical to `anyrepo foreach -- git pull`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "pull"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def push(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git push' on projects.

    This command behaves identical to `anyrepo foreach -- git push`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "push"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def rebase(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `anyrepo foreach -- git rebase`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "rebase"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@pass_context
def status(context, projects=None):
    """
    Run 'git status' (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(echo=context.echo)
        for status in arepo.status(project_paths=projects):
            context.echo(str(status))


@main.command()
@paths_argument()
@pass_context
def checkout(context, paths):
    """
    Run 'git checkout' on paths and choose the right git clone and manifest revision automatically.

    Checkout all clones to their manifest revision, if no paths are given.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(echo=context.echo)
        arepo.checkout([Path(path) for path in paths])


@main.command()
@paths_argument()
@pass_context
def add(context, paths):
    """
    Run 'git add' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(echo=context.echo)
        arepo.add([Path(path) for path in paths])


@main.command()
@paths_argument()
@pass_context
def reset(context, paths):
    """
    Run 'git reset' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(echo=context.echo)
        arepo.reset([Path(path) for path in paths])


@main.command()
@click.option("--message", "-m", help="commit message")
@paths_argument()
@pass_context
def commit(context, paths, message=None):
    """
    Run 'git commit' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        if not message:
            raise ValueError("Please provide a commit message.")
        arepo = AnyRepo.from_path(echo=context.echo)
        arepo.commit(message, [Path(path) for path in paths])


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def diff(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git diff' on projects.

    This command behaves identical to `anyrepo foreach -- git diff`.
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "diff"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def foreach(context, command, projects=None, manifest_path=None, groups=None):
    """
    Run 'command' on projects.

    Please use '--' to separate anyrepo command line options from options forwarded to the `command`
    (i.e. `anyrepo foreach -- ls -l`)
    """
    with exceptionhandling(context):
        arepo = AnyRepo.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(command, project_paths=projects, groups=groups)


main.add_command(manifest)
main.add_command(info)
