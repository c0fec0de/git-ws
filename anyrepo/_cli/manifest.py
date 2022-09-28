"""Manifest Commands."""
import click

from anyrepo import AnyRepo

from .util import exceptionhandling, pass_context


@click.group()
def manifest():
    """
    Manifest Information.
    """


@manifest.command()
@pass_context
def resolve(context):
    """
    Print The Manifest With All Imports Resolved.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        manifest = anyrepo.get_manifest(resolve=True)
        click.echo(manifest.dump())


@manifest.command()
@pass_context
def freeze(context):
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        manifest = anyrepo.get_manifest(freeze=True, resolve=True)
        click.echo(manifest.dump())


@manifest.command()
@pass_context
def validate(context):
    """
    Validate The Current Manifest, Exiting With An Error On Issues.
    """
    with exceptionhandling(context):
        AnyRepo.from_path()


@manifest.command()
@pass_context
def path(context):
    """
    Print Path to Main Manifest File.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        manifest = next(anyrepo.iter_manifests())
        click.echo(str(manifest.path))


@manifest.command()
@pass_context
def paths(context):
    """
    Print Paths to ALL Manifest Files.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        for manifest in anyrepo.iter_manifests():
            click.echo(str(manifest.path))
