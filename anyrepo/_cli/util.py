"""Command Line Interface Utilities."""
import traceback
from contextlib import contextmanager
from typing import Any, Optional

import click
from pydantic import BaseModel

from anyrepo import GitCloneMissingError, ManifestNotFoundError, NoGitError, UninitializedError


class Context(BaseModel):

    """Command Line Context."""

    verbose: int
    anyrepo: Optional[Any] = None


pass_context = click.make_pass_decorator(Context)


class Error(click.ClickException):
    """Common CLI Error."""

    def format_message(self) -> str:
        return click.style(self.message, fg="red")


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
        raise Error(f"{exc!s} Try:\n\n    anyrepo init\n\nor:\n\n    anyrepo clone\n") from None
    except NoGitError as exc:
        _print_traceback(context, exc)
        raise Error(f"{exc!s} Try:\n\n    git init\n\nor:\n\n    git clone\n") from None
    except ManifestNotFoundError as exc:
        _print_traceback(context, exc)
        raise Error(f"{exc!s} Try\n\n    anyrepo create-manifest --manifest='{exc.path!s}'\n") from None
    except GitCloneMissingError as exc:
        _print_traceback(context, exc)
        raise Error(f"{exc!s} Try\n\n    anyrepo update\n") from None
    except Exception as exc:
        _print_traceback(context, exc)
        raise Error(f"{exc!s}") from None


def _print_traceback(context: Context, exc: Exception):
    if context.verbose > 1:  # pragma: no cover
        # pylint: disable=no-value-for-parameter
        lines = "".join(traceback.format_exc())
        click.secho(lines, fg="red")
