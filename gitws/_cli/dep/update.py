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

from ..common import exceptionhandling, pass_context


@click.group()
def update():
    """
    Automatically Update Dependencies.
    """


@update.command()
@pass_context
@click.option("--recursive", "-r", is_flag=True, help="Update revisions in dependencies also")
def revision(context, recursive):
    """
    Update Revision.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path()
        gws.update_manifest(recursive=recursive, revision=True)
