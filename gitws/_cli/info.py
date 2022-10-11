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
