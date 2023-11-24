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

"""Update Commands."""

import click

from gitws import GitWS
from gitws._cli.common import exceptionhandling, pass_context

recursive_option = click.option(
    "--recursive", "-r", is_flag=True, help="Update all manifests, not just the main manifest"
)


@click.group(invoke_without_command=True)
@click.pass_context
@pass_context
@recursive_option
def update(context, ctx, recursive):
    """
    Automatically Update Revision and URL of Dependencies.
    """
    if not ctx.invoked_subcommand:
        with exceptionhandling(context):
            gws = GitWS.from_path()
            gws.update_manifest(recursive=recursive, revision=True, url=True)


@update.command()
@pass_context
@recursive_option
def revision(context, recursive):
    """
    Update Dependency Revisions.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path()
        gws.update_manifest(recursive=recursive, revision=True)


@update.command()
@pass_context
@recursive_option
def url(context, recursive):
    """
    Update Dependency URLs.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path()
        gws.update_manifest(recursive=recursive, url=True)
