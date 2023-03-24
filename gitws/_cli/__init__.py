# Copyright 2022-2023 c0fec0de
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

from gitws import AppConfig, Defaults, GitWS, ManifestSpec
from gitws._util import resolve_relative
from gitws.const import MANIFEST_PATH_DEFAULT
from gitws.git import FileStatus, State

from .common import COLOR_INFO, Context, Error, exceptionhandling, get_loglevel, pass_context
from .config import config
from .dep import dep
from .info import info
from .manifest import manifest
from .options import (
    command_option,
    command_options_option,
    force_option,
    group_filters_option,
    main_path_option,
    manifest_option,
    paths_argument,
    process_command,
    process_command_options,
    process_main_path,
    process_paths,
    projects_option,
    reverse_option,
    update_option,
    ws_path_option,
)
from .remote import remote

_LOGGING_FORMAT = "%(name)s %(levelname)s %(message)s"


def _version_option():  # pragma: no cover
    # Add support for click 7.x.x and click 8.x.x
    if click.version_option.__kwdefaults__ and "package_name" in click.version_option.__kwdefaults__:
        return click.version_option(package_name="git-ws")
    return click.version_option()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-v", "--verbose", count=True)
@_version_option()
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
@main_path_option()
@ws_path_option()
@manifest_option(initial=True)
@group_filters_option(initial=True)
@update_option()
@force_option()
@pass_context
def init(
    context,
    ws_path=None,
    main_path=None,
    manifest_path=None,
    group_filters=None,
    update: bool = False,
    force: bool = False,
):
    """
    Initialize Git Workspace *with* or *without* main project.

    *with* main project: run `git ws init` in the directory of an actual git clone OR
    run `git ws init PATH_TO_MAIN_GIT_CLONE`. The git clone becomes the main project
    in both cases.

    *without* main project: run `git ws init` in the intended workspace directory.
    No main git project is needed.

    In any of these cases a manifest file (i.e. `git-ws.toml`) is required.
    It can be created via `git ws manifest create`.
    """
    with exceptionhandling(context):
        main_path = process_main_path(main_path)
        gws = GitWS.init(
            path=ws_path,
            main_path=main_path,
            manifest_path=manifest_path,
            group_filters=group_filters,
            force=force,
            secho=context.secho,
        )
        click.secho(f"Workspace initialized at {str(resolve_relative(gws.path))!r}.")
        if update:
            gws.update(skip_main=True)
        else:
            click.secho("Please continue with:\n\n    git ws update\n", fg=COLOR_INFO)


@main.command()
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
@force_option()
@pass_context
def deinit(context, prune: bool = False, force: bool = False):
    """
    Deinitialize Git Workspace.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(secho=context.secho)
        gws.deinit(prune=prune, force=force)
        click.secho(f"Workspace deinitialized at {str(resolve_relative(gws.path))!r}.")


@main.command()
@click.argument("url")
@main_path_option()
@ws_path_option(nomain=True)
@manifest_option(initial=True)
@group_filters_option(initial=True)
@click.option("--revision", help="Revision to be checked out. Tag, Branch or SHA")
@update_option()
@force_option()
@pass_context
def clone(
    context,
    url,
    ws_path=None,
    main_path=None,
    manifest_path=None,
    group_filters=None,
    revision=None,
    update: bool = False,
    force: bool = False,
):
    """
    Create a git clone from URL and initialize Git Workspace.

    MAIN_PATH is optional. If not specified `REPONAME/REPONAME/` by default.
    """
    with exceptionhandling(context):
        main_path = process_main_path(main_path)
        gws = GitWS.clone(
            url,
            path=ws_path,
            main_path=main_path,
            manifest_path=manifest_path,
            group_filters=group_filters,
            revision=revision,
            force=force,
            secho=context.secho,
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
@group_filters_option()
@click.option("--skip-main", "-S", is_flag=True, default=False, help="Skip Main Repository")
@click.option("--rebase", is_flag=True, default=False, help="Run 'git rebase' instead of 'git pull'")
@click.option("--prune", is_flag=True, default=False, help="Remove obsolete git clones")
@force_option()
@pass_context
def update(
    context,
    projects=None,
    manifest_path=None,
    group_filters=None,
    skip_main: bool = False,
    rebase: bool = False,
    prune: bool = False,
    force: bool = False,
):
    """Create/update all dependent git clones."""
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.update(
            project_paths=projects,
            skip_main=skip_main,
            rebase=rebase,
            prune=prune,
            force=force,
        )


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@reverse_option()
@command_option
@pass_context
def git(context, command, projects=None, manifest_path=None, group_filters=None, reverse=False):
    """
    Run git COMMAND on projects.

    This command is identical to `git ws foreach -- git COMMAND`.
    """
    with exceptionhandling(context):
        command = process_command(command)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git",) + command, project_paths=projects, reverse=reverse)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@command_options_option
@pass_context
def fetch(context, command_options=None, projects=None, manifest_path=None, group_filters=None):
    """
    Run 'git fetch' on projects.

    This command is identical to `git ws foreach -- git fetch COMMAND_OPTIONS`.
    """
    with exceptionhandling(context):
        command_options = process_command_options(command_options)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git", "fetch") + command_options, project_paths=projects)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@command_options_option
@pass_context
def pull(context, command_options=None, projects=None, manifest_path=None, group_filters=None):
    """
    Run 'git pull' on projects.

    This command is identical to `git ws foreach -- git pull COMMAND_OPTIONS`.
    """
    with exceptionhandling(context):
        command_options = process_command_options(command_options)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git", "pull") + command_options, project_paths=projects)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@command_options_option
@pass_context
def push(context, command_options=None, projects=None, manifest_path=None, group_filters=None):
    """
    Run 'git push' on projects (in reverse order).

    This command is identical to `git ws foreach --reverse -- git push COMMAND_OPTIONS`.
    """
    with exceptionhandling(context):
        command_options = process_command_options(command_options)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git", "push") + command_options, project_paths=projects, reverse=True)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@command_options_option
@pass_context
def rebase(context, command_options=None, projects=None, manifest_path=None, group_filters=None):
    """
    Run 'git rebase' on projects.

    This command is identical to `git ws foreach -- git rebase COMMAND_OPTIONS`.
    """
    with exceptionhandling(context):
        command_options = process_command_options(command_options)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git", "rebase") + command_options, project_paths=projects)


@main.command()
@paths_argument()
@click.option("--branch", "-b", is_flag=True, help="show branch information")
@click.option("--banner", "-B", is_flag=True, help="show banner of each project")
@manifest_option()
@group_filters_option()
@pass_context
def status(context, manifest_path=None, group_filters=None, paths=None, branch: bool = False, banner: bool = False):
    """
    Run 'git status' on PATHS or all files (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        for status in gws.status(paths=process_paths(paths), branch=branch, banner=banner):
            text = str(status)
            if isinstance(status, FileStatus):
                fgidx = "red" if status.work in (State.IGNORED, State.UNTRACKED) else "green"
                parts = (
                    context.style(text[0], fg=fgidx),
                    context.style(text[1], fg="red"),
                    text[2:],
                )
                click.echo("".join(parts))
            else:
                click.echo(text)


@main.command()
@paths_argument()
@click.option("--stat", "stat", is_flag=True, help="show diffstat instead of patch.")
@manifest_option()
@group_filters_option()
@pass_context
def diff(context, manifest_path=None, group_filters=None, paths=None, stat=False):
    """
    Run 'git diff' on PATHS or all files (displayed paths include the actual clone path).
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        if stat:
            for diffstat in gws.diffstat(paths=process_paths(paths)):
                click.echo(str(diffstat))
        else:
            gws.diff(paths=process_paths(paths))


@main.command()
@paths_argument()
@force_option()
@manifest_option()
@group_filters_option()
@pass_context
def checkout(context, manifest_path=None, group_filters=None, paths=None, force: bool = False):
    """
    Run 'git checkout' on PATHS and choose the right git clone and manifest revision automatically.

    Checkout all clones to their manifest revision, if no paths are given.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.checkout(process_paths(paths), force=force)


@main.command()
@paths_argument()
@click.option("--force", "-f", "force", is_flag=True, help="allow adding otherwise ignored files")
@click.option("--all", "-A", "all_", is_flag=True, help="add changes from all tracked and untracked files")
@manifest_option()
@group_filters_option()
@pass_context
def add(context, manifest_path=None, group_filters=None, paths=None, force=False, all_=False):
    """
    Run 'git add' on PATHS and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.add(process_paths(paths), force=force, all_=all_)


# pylint: disable=invalid-name
@main.command()
@paths_argument()
@force_option()
@click.option("--cached", "cached", is_flag=True, help="only remove from index")
@click.option("-r", "recursive", is_flag=True, help="allow recursive removal")
@manifest_option()
@group_filters_option()
@pass_context
def rm(context, manifest_path=None, group_filters=None, paths=None, force=False, cached=False, recursive=False):
    """
    Run 'git rm' on PATHS and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.rm(process_paths(paths), force=force, cached=cached, recursive=recursive)


@main.command()
@paths_argument()
@manifest_option()
@group_filters_option()
@pass_context
def reset(context, manifest_path=None, group_filters=None, paths=None):
    """
    Run 'git reset' on PATHS and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.reset(process_paths(paths))


@main.command()
@click.option("--message", "-m", help="commit message")
@click.option("--all", "-a", "all_", is_flag=True, help="commit all changed files")
@paths_argument()
@manifest_option()
@group_filters_option()
@pass_context
def commit(context, manifest_path=None, group_filters=None, paths=None, message=None, all_=False):
    """
    Run 'git commit' on PATHS and choose the right git clone automatically.
    """
    with exceptionhandling(context):
        if not message:
            raise ValueError("Please provide a commit message.")
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.commit(message, process_paths(paths), all_=all_)


@main.command()
@click.argument("name")
@click.option("--message", "-m", help="tag message")
@click.option("--force", "-f", is_flag=True, help="replace the tag if exists")
@manifest_option()
@group_filters_option()
@pass_context
def tag(context, name, manifest_path=None, group_filters=None, message=None, force=None):
    """
    Create git tag NAME on main repository.

    This includes freezing all dependencies.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.tag(name, msg=message, force=force)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@reverse_option()
@command_option
@pass_context
def foreach(context, command, projects=None, manifest_path=None, group_filters=None, reverse=False):
    """
    Run COMMAND on projects.

    Please use '--' to separate 'git ws' command line options from options forwarded to the COMMAND
    (i.e. `git ws foreach -- ls -l`)
    """
    with exceptionhandling(context):
        command = process_command(command)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(command, project_paths=projects, reverse=reverse)


@main.command()
@projects_option()
@manifest_option()
@group_filters_option()
@reverse_option()
@command_option
@pass_context
def submodule(context, command, projects=None, manifest_path=None, group_filters=None, reverse=False):
    """
    Run git submodule COMMAND on projects.

    This command is identical to `git ws foreach -- git submodule COMMAND`.
    """
    with exceptionhandling(context):
        command = process_command(command)
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters, secho=context.secho)
        gws.run_foreach(("git", "submodule") + command, project_paths=projects, reverse=reverse)


@main.command()
@manifest_option(initial=True)
@click.argument("name", type=click.Choice(tuple(Defaults().dict(by_alias=True))))
@click.argument("value")
@pass_context
def default(context, manifest_path, name, value):
    """
    Set DEFAULT in Manifest to VALUE.
    """
    with exceptionhandling(context):
        manifest_path = Path(manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        defaults = manifest_spec.defaults.update_fromstr({name: value if value else None})
        manifest_spec = manifest_spec.update(defaults=defaults)
        manifest_spec.save(manifest_path)


@main.command()
@manifest_option(initial=True)
@click.argument("value")
@pass_context
def group_filters(context, manifest_path, value):
    """
    Set Group Filter to VALUE.

    The group filter selects/deselects dependencies based on their path and/or groups.
    """
    with exceptionhandling(context):
        manifest_path = Path(manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        manifest_spec = manifest_spec.update_fromstr({"group-filters": value if value else None})
        manifest_spec.save(manifest_path)


main.add_command(config)
main.add_command(info)
main.add_command(manifest)
main.add_command(remote)
main.add_command(dep)
