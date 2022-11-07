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
from anytree import ContStyle, RenderTree

from gitws import GitWS

from ..deptree import DepDotExporter
from .common import exceptionhandling, pass_context
from .options import group_filters_option, manifest_option


@click.group()
def info():
    """
    Git Workspace Information.
    """


@info.command()
@pass_context
def workspace_path(context):
    """
    Print Path to Workspace.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path()
        click.echo(str(gws.path))


@info.command()
@pass_context
def main_path(context):
    """
    Print Path to Main Git Clone.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path()
        click.echo(str(gws.workspace.main_path))


@info.command()
@manifest_option()
@group_filters_option()
@pass_context
def project_paths(context, manifest_path=None, group_filters=None):
    """
    Print Paths to all git clones.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        for project in gws.projects():
            project_path = gws.workspace.get_project_path(project)
            click.echo(project_path)


@info.command()
@manifest_option()
@group_filters_option()
@click.option("--dot", "-d", "dot", is_flag=True, help="Export DOT Format to be forwarded to graphviz.")
@click.option("--primary", "-p", is_flag=True, help="Display primary dependencies only.")
@pass_context
def dep_tree(context, manifest_path=None, group_filters=None, dot: bool = False, primary: bool = False):
    """
    Print Dependency Tree.

    The standard output on '--dot' can be directly forwarded to `graphviz`'s tool `dot`.
    Example:

    $ git ws info dep-tree --dot | dot -Tpng > dep-tree.png

    $ git ws info dep-tree --dot | dot -Tsvg > dep-tree.svg
    """

    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        deptree = gws.get_deptree(primary=primary)
        if dot:
            click.echo("\n".join(DepDotExporter(deptree)))
        else:
            for pre, _, node in RenderTree(deptree, style=ContStyle()):
                info = "" if node.is_primary else "*"
                click.echo(f"{pre}{node.project.info}{info}")
