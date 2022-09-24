"""Command Line Interface Utilities."""
from contextlib import contextmanager

import click

from anyrepo import ManifestNotFoundError, NoGitError, UninitializedError


@contextmanager
def exceptionhandling():
    """
    Click Exception Handling.

    The AnyRepo implementation shall NOT depend on click (except the cli module).
    Therefore we remap any internal errors to nice click errors.

    We provide useful command line hints, depending on exceptions.
    """
    try:
        yield
    except UninitializedError as exc:
        raise click.ClickException(f"{exc!s}\nTry:\n\nanyrepo init\n\nor:\n\nanyrepo clone\n")
    except NoGitError as exc:
        raise click.ClickException(f"{exc!s}\nTry:\n\ngit init\n\nor:\n\ngit clone\n")
    except ManifestNotFoundError as exc:
        raise click.ClickException(f"{exc!s}\nTry\n\nanyrepo create-manifest --manifest='{exc.path!s}'")
    except Exception as exc:
        raise click.ClickException(f"{exc!s}")


def banner(text):
    """Banner."""
    click.secho(f"===== {text} =====", fg="green")
