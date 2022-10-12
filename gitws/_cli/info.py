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

"""Info Commands."""

import click

from gitws import GitWS

from .common import exceptionhandling, pass_context
from .options import groups_option, manifest_option


@click.group()
def info():
    """
    Git Workspace Information.
    """


@info.command()
@manifest_option()
@pass_context
def workspace_path(context, manifest_path=None):
    """
    Print Path to Workspace.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path)
        context.echo(str(gws.path))


@info.command()
@manifest_option()
@pass_context
def main_path(context, manifest_path=None):
    """
    Print Path to Main Git Clone.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path)
        context.echo(str(gws.workspace.main_path))


@info.command()
@manifest_option()
@groups_option()
@pass_context
def project_paths(context, manifest_path=None, groups=None):
    """
    Print Paths to all git clones.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path)
        for project in gws.projects(filter_=gws.create_groups_filter(groups)):
            project_path = gws.workspace.get_project_path(project)
            context.echo(project_path)
