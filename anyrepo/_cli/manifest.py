"""Manifest Commands."""
import click


@click.group()
def manifest():
    """
    Manifest Information.
    """


@manifest.command()
def resolve():
    """
    Print The Manifest With All Imports Resolved.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    click.echo("TODO: Manifest Resolve")


@manifest.command()
def freeze():
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    click.echo("TODO: Manifest Freeze")


@manifest.command()
def validate():
    """
    Validate The Current Manifest, Exiting With An Error On Issues.
    """
    click.echo("TODO: Manifest Validate")


@manifest.command()
def path():
    """
    Print Path to Main Manifest File.
    """
    click.echo("TODO: Manifest Path")


@manifest.command()
def paths():
    """
    Print Paths to ALL Manifest Files.
    """
    click.echo("TODO: Manifest Paths")
