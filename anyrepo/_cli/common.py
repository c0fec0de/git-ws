"""Command Line Interface Utilities."""
import logging
import traceback
from contextlib import contextmanager

import click
from pydantic import BaseModel

from anyrepo import GitCloneMissingError, GitCloneNotCleanError, ManifestNotFoundError, NoGitError, UninitializedError

COLOR_INFO = "blue"


_LOGLEVELMAP = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def get_loglevel(verbose: int):
    """Return `logging.level` according to verbosity."""
    return _LOGLEVELMAP.get(verbose, logging.DEBUG)


class Context(BaseModel):

    """Command Line Context."""

    verbose: int
    color: bool

    def echo(self, *args, **kwargs):
        """Print with color support similar to :any:`click.secho()."""
        if self.color:
            return click.secho(*args, **kwargs)
        return click.echo(*args)


pass_context = click.make_pass_decorator(Context)


class Error(click.ClickException):
    """Common CLI Error."""

    color = True

    def format_message(self) -> str:
        if self.color:
            return click.style(self.message, fg="red")
        return self.message


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
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    anyrepo init\n\nor:\n\n    anyrepo clone\n") from None
    except NoGitError as exc:
        _print_traceback(context)
        raise Error(
            f"{exc!s} Change to your existing git clone or try:\n\n    git init\n\nor:\n\n    git clone\n"
        ) from None
    except ManifestNotFoundError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    anyrepo manifest create --manifest='{exc.path!s}'\n") from None
    except GitCloneMissingError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    anyrepo update\n") from None
    except GitCloneNotCleanError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s}\n\nCommit/Push all your changes and branches or use '--force'\n") from None
    except Exception as exc:
        _print_traceback(context)
        raise Error(f"{exc!s}") from None


def _print_traceback(context: Context):
    if context.verbose > 1:  # pragma: no cover
        # pylint: disable=no-value-for-parameter
        lines = "".join(traceback.format_exc())
        context.echo(lines, fg="red", err=True)
