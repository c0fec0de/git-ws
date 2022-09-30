"""Info Commands."""

import click

from anyrepo import AnyRepo

from .options import groups_option
from .util import exceptionhandling, pass_context


@click.group()
def info():
    """
    AnyRepo Information.
    """


@info.command()
@pass_context
def workspace_path(context):
    """
    Print Path to Workspace.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        click.echo(str(anyrepo.path))


@info.command()
@groups_option()
@pass_context
def project_paths(context, groups):
    """
    Print Paths to all git clones.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        for project in anyrepo.iter_projects(filter_=anyrepo.create_groups_filter(groups)):
            project_path = anyrepo.workspace.get_project_path(project)
            click.echo(project_path)
