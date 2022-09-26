"""Manifest Commands."""
import click


@click.group()
def manifest():
    """
    Manifest Information.
    """


@click.command()
def resolve():
    """
    Print The Manifest With All Imports Resolved.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    click.echo("TODO: Manifest Resolve")


@click.command()
def freeze():
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    click.echo("TODO: Manifest Freeze")


@click.command()
def validate():
    """
    Validate The Current Manifest, Exiting With An Error On Issues.
    """
    click.echo("TODO: Manifest Validate")


@click.command()
def path():
    """
    Print Path to Main Manifest File.
    """
    click.echo("TODO: Manifest Path")


@click.command()
def paths():
    """
    Print Paths to ALL Manifest Files.
    """
    click.echo("TODO: Manifest Paths")


manifest.add_command(resolve)
manifest.add_command(freeze)
manifest.add_command(validate)
manifest.add_command(path)
manifest.add_command(paths)
