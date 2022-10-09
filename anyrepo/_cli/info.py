"""Info Commands."""

import click

from anyrepo import AnyRepo

from .common import exceptionhandling, pass_context
from .options import groups_option, manifest_option


@click.group()
def info():
    """
    AnyRepo Information.
    """


@info.command()
@manifest_option()
@pass_context
def workspace_path(context, manifest_path=None):
    """
    Print Path to Workspace.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        context.echo(str(anyrepo.path))


@info.command()
@manifest_option()
@pass_context
def main_path(context, manifest_path=None):
    """
    Print Path to Main Git Clone.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        context.echo(str(anyrepo.workspace.main_path))


@info.command()
@manifest_option()
@groups_option()
@pass_context
def project_paths(context, manifest_path=None, groups=None):
    """
    Print Paths to all git clones.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        for project in anyrepo.projects(filter_=anyrepo.create_groups_filter(groups)):
            project_path = anyrepo.workspace.get_project_path(project)
            context.echo(project_path)
