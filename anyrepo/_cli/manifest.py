"""Manifest Commands."""
from pathlib import Path

import click

from anyrepo import AnyRepo, ManifestSpec

from .common import COLOR_INFO, exceptionhandling, pass_context
from .options import groups_option, manifest_option, output_option


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
            context.echo(manifest.dump())


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
            context.echo(manifest.dump())


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
        context.echo(str(manifest.path))


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
            context.echo(str(manifest.path))


@manifest.command()
@manifest_option(initial=True)
@pass_context
def create(context, manifest_path):
    """Create Manifest."""
    with exceptionhandling(context):
        path = AnyRepo.create_manifest(Path(manifest_path))
        click.secho(f"Manifest {str(path)!r} created.", fg=COLOR_INFO)


@manifest.command()
@manifest_option(initial=True)
@pass_context
def upgrade(context, manifest_path):
    """
    Update Manifest To Latest Version.

    User data is kept.
    User comments are removed.
    Comments are updated to the latest documentation.
    """
    with exceptionhandling(context):
        ManifestSpec.upgrade(Path(manifest_path))
        click.secho(f"Manifest {str(manifest_path)!r} upgraded.", fg=COLOR_INFO)
