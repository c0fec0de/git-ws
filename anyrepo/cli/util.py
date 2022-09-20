"""Command Line Interface Utilities."""
from contextlib import contextmanager

import click


@contextmanager
def exceptionhandling():
    """
    Click Exception Handling.

    The AnyRepo implementation shall NOT depend on click (except the cli module).
    Therefore we remap any internal errors to nice click errors.
    """
    try:
        yield
    except RuntimeError as exc:
        raise click.ClickException(str(exc))


def banner(text):
    """Banner."""
    click.secho(f"===== {text} =====", fg="green")
