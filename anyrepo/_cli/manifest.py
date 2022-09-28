"""Manifest Commands."""
from pathlib import Path

import click

from anyrepo import AnyRepo

from .util import exceptionhandling, pass_context


def _output_option():
    return click.option(
        "--output",
        "-O",
        "output",
        type=click.Path(dir_okay=False),
        help="Write Manifest to file instead of STDOUT.",
    )


@click.group()
def manifest():
    """
    Manifest Information.
    """


@manifest.command()
@_output_option()
@pass_context
def resolve(context, output=None):
    """
    Print The Manifest With All Imports Resolved.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        manifest = anyrepo.get_manifest_spec(resolve=True)
        if output:
            manifest.save(Path(output))
        else:
            click.echo(manifest.dump())


@manifest.command()
@_output_option()
@pass_context
def freeze(context, output=None):
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path()
        manifest = anyrepo.get_manifest_spec(freeze=True, resolve=True)
        if output:
            manifest.save(Path(output))
        else:
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
