"""Command Line Interface."""
import click

from .manifest import manifest


@click.group()
def main():
    """
    Multi Repository Management Tool.
    """


@click.command()
def clone():
    """Run 'git clone'."""
    click.echo("TODO: clone")


@click.command()
def fetch():
    """Run 'git fetch'."""
    click.echo("TODO: fetch")


@click.command()
def pull():
    """Run 'git pull'."""
    click.echo("TODO: pull")


@click.command()
def rebase():
    """Run 'git rebase'."""
    click.echo("TODO: rebase")


@click.command()
def status():
    """Run 'git status'."""
    click.echo("TODO: status")


@click.command()
def forall():
    """Run 'git forall'."""
    click.echo("TODO: forall")


main.add_command(manifest)
