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
from gitws.git import FileStatus, State

from .common import COLOR_INFO, Context, Error, exceptionhandling, get_loglevel, pass_context
from .config import config
from .info import info
from .manifest import manifest
from .options import (
    force_option,
    groups_option,
    manifest_option,
    path_option,
    paths_argument,
    process_path,
    process_paths,
    projects_option,
    reverse_option,
    update_option,
)

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
@path_option()
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@force_option()
@pass_context
def init(context, path=None, manifest_path=None, groups=None, update: bool = False, force: bool = False):
    """
    Initialize Git Workspace.

    The actual directory MUST be a valid git clone, which has been
    be either created by 'git init' or 'git clone'.
    """
    with exceptionhandling(context):
        path = process_path(path)
        gws = GitWS.init(main_path=path, manifest_path=manifest_path, groups=groups, force=force, secho=context.secho)
        click.secho(f"Workspace initialized at {str(resolve_relative(gws.path))!r}.")
        if update:
            gws.update(skip_main=True)
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
        gws = GitWS.from_path(secho=context.secho)
        gws.deinit()
        click.secho(f"Workspace deinitialized at {str(resolve_relative(gws.path))!r}.")


@main.command()
@click.argument("url")
@path_option()
@manifest_option(initial=True)
@groups_option(initial=True)
@update_option()
@force_option()
@pass_context
def clone(context, url, path=None, manifest_path=None, groups=None, update: bool = False, force: bool = False):
    """
    Create a git clone and initialize Git Workspace.
    """
    with exceptionhandling(context):
        path = process_path(path)
        gws = GitWS.clone(
            url, main_path=path, manifest_path=manifest_path, groups=groups, force=force, secho=context.secho
        )
        if update:
            gws.update(skip_main=True)
        else:
            click.secho(
                f"Workspace initialized at {str(resolve_relative(gws.path))!r}. "
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
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.update(
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
@reverse_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def git(context, command, projects=None, manifest_path=None, groups=None, reverse=False):
    """
    Run git command on projects.

    This command behaves identical to `git ws foreach -- git`.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(("git",) + command, project_paths=projects, groups=groups, reverse=reverse)


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
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(("git", "fetch"), project_paths=projects, groups=groups)


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
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(("git", "pull"), project_paths=projects, groups=groups)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@pass_context
def push(context, projects=None, manifest_path=None, groups=None):
    """
    Run 'git push' on projects (in reverse order).

    This command behaves identical to `git ws foreach --reverse -- git push`.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(("git", "push"), project_paths=projects, groups=groups, reverse=True)


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
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(("git", "rebase"), project_paths=projects, groups=groups)


@main.command()
@paths_argument()
@click.option("--branch", "-b", is_flag=True, help="show branch information")
@pass_context
def status(context, paths=None, branch: bool = False):
    """
    Run 'git status' (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        for status in gws.status(paths=process_paths(paths), branch=branch):
            text = str(status)
            if isinstance(status, FileStatus):
                fgidx = "red" if status.work in (State.IGNORED, State.UNTRACKED) else "green"
                parts = (
                    context.style(text[0], fg="red"),
                    context.style(text[1], fg=fgidx),
                    text[2:],
                )
                click.echo("".join(parts))
            else:
                click.echo(text)


@main.command()
@paths_argument()
@click.option("--stat", "stat", is_flag=True, help="show diffstat instead of patch.")
@pass_context
def diff(context, paths=None, stat=False):
    """
    Run 'git diff' on paths (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        if stat:
            for diffstat in gws.diffstat(paths=process_paths(paths)):
                click.echo(str(diffstat))
        else:
            gws.diff(paths=process_paths(paths))


@main.command()
@paths_argument()
@force_option()
@pass_context
def checkout(context, paths=None, force: bool = False):
    """
    Run 'git checkout' on paths and choose the right git clone and manifest revision automatically.

    Checkout all clones to their manifest revision, if no paths are given.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        gws.checkout(process_paths(paths), force=force)


@main.command()
@paths_argument()
@pass_context
@click.option("--force", "-f", "force", is_flag=True, help="allow adding otherwise ignored files")
@click.option("--all", "-A", "all_", is_flag=True, help="add changes from all tracked and untracked files")
def add(context, paths=None, force=False, all_=False):
    """
    Run 'git add' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        gws.add(process_paths(paths), force=force, all_=all_)


# pylint: disable=invalid-name
@main.command()
@paths_argument()
@force_option()
@click.option("--cached", "cached", is_flag=True, help="only remove from index")
@click.option("-r", "recursive", is_flag=True, help="allow recursive removal")
@pass_context
def rm(context, paths=None, force=False, cached=False, recursive=False):
    """
    Run 'git rm' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        gws.rm(process_paths(paths), force=force, cached=cached, recursive=recursive)


@main.command()
@paths_argument()
@pass_context
def reset(context, paths=None):
    """
    Run 'git reset' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        gws.reset(process_paths(paths))


@main.command()
@click.option("--message", "-m", help="commit message")
@click.option("--all", "-a", "all_", is_flag=True, help="commit all changed files")
@paths_argument()
@pass_context
def commit(context, paths=None, message=None, all_=False):
    """
    Run 'git commit' on paths and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        if not message:
            raise ValueError("Please provide a commit message.")
        gws = GitWS.from_path(secho=context.secho)
        gws.commit(message, process_paths(paths), all_=all_)


@main.command()
@projects_option()
@manifest_option()
@groups_option()
@reverse_option()
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@pass_context
def foreach(context, command, projects=None, manifest_path=None, groups=None, reverse=False):
    """
    Run 'command' on projects.

    Please use '--' to separate 'git ws' command line options from options forwarded to the `command`
    (i.e. `git ws foreach -- ls -l`)
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, secho=context.secho)
        gws.run_foreach(command, project_paths=projects, groups=groups, reverse=reverse)


main.add_command(config)
main.add_command(info)
main.add_command(manifest)
