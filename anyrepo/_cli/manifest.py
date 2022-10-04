"""Manifest Commands."""
from pathlib import Path

import click

from anyrepo import AnyRepo

from .options import groups_option, manifest_option, output_option
from .util import exceptionhandling, pass_context


@click.group()
def manifest():
    """
    Manifest Information.
    """


@manifest.command()
@manifest_option()
@groups_option()
@output_option()
@pass_context
def resolve(context, manifest_path=None, groups=None, output=None):
    """
    Print The Manifest With All Imports Resolved.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        manifest = anyrepo.get_manifest_spec(groups=groups, resolve=True)
        if output:
            manifest.save(Path(output))
        else:
            click.echo(manifest.dump())


@manifest.command()
@manifest_option()
@groups_option()
@output_option()
@pass_context
def freeze(context, manifest_path=None, groups=None, output=None):
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        manifest = anyrepo.get_manifest_spec(groups=groups, freeze=True, resolve=True)
        if output:
            manifest.save(Path(output))
        else:
            click.echo(manifest.dump())


@manifest.command()
@manifest_option()
@pass_context
def validate(context, manifest_path=None):
    """
    Validate The Current Manifest, Exiting With An Error On Issues.
    """
    with exceptionhandling(context):
        AnyRepo.from_path(manifest_path=manifest_path)


@manifest.command()
@manifest_option()
@pass_context
def path(context, manifest_path=None):
    """
    Print Path to Main Manifest File.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        manifest = next(anyrepo.manifests())
        click.echo(str(manifest.path))


@manifest.command()
@manifest_option()
@pass_context
def paths(context, manifest_path=None):
    """
    Print Paths to ALL Manifest Files.
    """
    with exceptionhandling(context):
        anyrepo = AnyRepo.from_path(manifest_path=manifest_path)
        for manifest in anyrepo.manifests():
            click.echo(str(manifest.path))
