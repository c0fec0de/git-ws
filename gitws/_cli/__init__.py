# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Command Line Interface."""
import logging
from pathlib import Path

import click
import coloredlogs  # type: ignore

from gitws import AppConfig, GitWS
from gitws._util import resolve_relative
from gitws.const import MANIFEST_PATH_DEFAULT

from .common import COLOR_INFO, Context, Error, exceptionhandling, get_loglevel, pass_context
from .config import config
from .info import info
from .manifest import manifest
from .options import force_option, groups_option, manifest_option, paths_argument, projects_option, update_option

_LOGGING_FORMAT = "%(name)s %(levelname)s %(message)s"


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True)
@click.version_option(package_name="git-ws")
@click.pass_context
def main(ctx=None, verbose=0):
    """
    Git Workspace - Multi Repository Management Tool.
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
@force_option()
@pass_context
def init(context, manifest_path=None, groups=None, update: bool = False, force: bool = False):
    """
    Initialize Git Workspace and create all dependent git clones.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling(context):
        arepo = GitWS.init(manifest_path=manifest_path, groups=groups, force=force, echo=context.echo)
        click.secho(f"Workspace initialized at {str(resolve_relative(arepo.path))!r}.")
        if update:
            arepo.update(skip_main=True)
        else:
            click.secho(
                "Please continue with:\n\n    git ws update\n",
                fg=COLOR_INFO,
            )


@main.command()
@pass_context
def deinit(context):
    """
    Deinitialize Git Workspace.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(echo=context.echo)
        arepo.deinit()
        click.secho(f"Workspace deinitialized at {str(resolve_relative(arepo.path))!r}.")


@main.command()
@click.argument("url")
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@force_option()
@pass_context
def clone(context, url, manifest_path=None, groups=None, update: bool = False, force: bool = False):
    """
    Create a git clone, initialize Git Workspace and create all dependent git clones.
    """
    with exceptionhandling(context):
        arepo = GitWS.clone(url, manifest_path=manifest_path, groups=groups, force=force, echo=context.echo)
        if update:
            arepo.update(skip_main=True)
        else:
            click.secho(
                f"Workspace initialized at {str(resolve_relative(arepo.path))!r}. "
                "Please continue with:\n\n    git ws update\n",
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
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
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

    This command behaves identical to `git ws foreach -- git`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git",) + command, project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def fetch(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git fetch' on projects.

    This command behaves identical to `git ws foreach -- git fetch`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "fetch"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def pull(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git pull' on projects.

    This command behaves identical to `git ws foreach -- git pull`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "pull"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def push(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git push' on projects.

    This command behaves identical to `git ws foreach -- git push`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "push"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def rebase(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git rebase' on projects.

    This command behaves identical to `git ws foreach -- git rebase`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(("git", "rebase"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@click.option("--branch", "-b", is_flag=True, help="show branch information")
@pass_context
def status(context, projects=None, branch: bool = False):
    """
    Run 'git status' (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(echo=context.echo)
        for status in arepo.status(project_paths=projects, branch=branch):
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
        arepo = GitWS.from_path(echo=context.echo)
        arepo.checkout([Path(path) for path in paths])


@main.command()
@paths_argument()
@pass_context
def add(context, paths):
    """
    Run 'git add' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(echo=context.echo)
        arepo.add([Path(path) for path in paths])


@main.command()
@paths_argument()
@pass_context
def reset(context, paths):
    """
    Run 'git reset' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(echo=context.echo)
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
        arepo = GitWS.from_path(echo=context.echo)
        arepo.commit(message, [Path(path) for path in paths])


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def diff(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git diff' on projects.

    This command behaves identical to `git ws foreach -- git diff`.
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
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

    Please use '--' to separate 'git ws' command line options from options forwarded to the `command`
    (i.e. `git ws foreach -- ls -l`)
    """
    with exceptionhandling(context):
        arepo = GitWS.from_path(manifest_path=manifest_path, echo=context.echo)
        arepo.run_foreach(command, project_paths=projects, groups=groups)


main.add_command(config)
main.add_command(info)
main.add_command(manifest)
