"""Command Line Interface Utilities."""
import traceback
from contextlib import contextmanager

import click
from pydantic import BaseModel

from anyrepo import ManifestNotFoundError, NoGitError, UninitializedError


class Context(BaseModel):

    """Command Line Context."""

    verbose: int


pass_context = click.make_pass_decorator(Context)


@contextmanager
def exceptionhandling(context: Context):
    """
    Click Exception Handling.

    The AnyRepo implementation shall NOT depend on click (except the cli module).
    Therefore we remap any internal errors to nice click errors.

    We provide useful command line hints, depending on exceptions.
    """
    try:
        yield
    except UninitializedError as exc:
        _print_traceback(context, exc)
        raise click.ClickException(f"{exc!s}\nTry:\n\nanyrepo init\n\nor:\n\nanyrepo clone")
    except NoGitError as exc:
        _print_traceback(context, exc)
        raise click.ClickException(f"{exc!s}\nTry:\n\ngit init\n\nor:\n\ngit clone")
    except ManifestNotFoundError as exc:
        _print_traceback(context, exc)
        raise click.ClickException(f"{exc!s}\nTry\n\nanyrepo create-manifest --manifest='{exc.path!s}'")
    except Exception as exc:
        _print_traceback(context, exc)
        raise click.ClickException(f"{exc!s}")


def _print_traceback(context: Context, exc: Exception):
    if context.verbose > 1:
        lines = "".join(traceback.format_exception(exc))
        click.secho(lines, fg="red")


def banner(text):
    """Banner."""
    click.secho(f"===== {text} =====", fg="green")
