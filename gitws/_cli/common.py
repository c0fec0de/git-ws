# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Command Line Interface Utilities."""
import logging
import shlex
import traceback
from contextlib import contextmanager
from subprocess import CalledProcessError

import click
from pydantic import BaseModel

from gitws import (
    GitCloneMissingError,
    GitCloneMissingOriginError,
    GitCloneNotCleanError,
    GitTagExistsError,
    ManifestNotFoundError,
    NoGitError,
    UninitializedError,
    WorkspaceNotEmptyError,
)

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

    def secho(self, message, **kwargs):
        """Print with color support similar to :any:`click.secho()."""
        if self.color:
            return click.secho(message, **kwargs)
        return click.echo(message)

    def style(self, text, **kwargs):
        """Format `text`."""
        if self.color:
            return click.style(text, **kwargs)
        return text


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

    The GitWS implementation shall NOT depend on click (except the cli module).
    Therefore we remap any internal errors to nice click errors.

    We provide useful command line hints, depending on exceptions.
    """
    try:
        yield
    except UninitializedError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    git ws init\n\nor:\n\n    git ws clone\n") from None
    except NoGitError as exc:
        _print_traceback(context)
        raise Error(
            f"{exc!s} Change to your existing git clone or try:\n\n    git init\n\nor:\n\n    git clone\n"
        ) from None
    except ManifestNotFoundError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    git ws manifest create --manifest='{exc.path!s}'\n") from None
    except GitCloneMissingError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    git ws update\n") from None
    except GitCloneNotCleanError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s}\n\nCommit/Push all your changes and branches or use '--force'\n") from None
    except WorkspaceNotEmptyError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s}\n\nChoose an empty directory or use '--force'\n") from None
    except GitCloneMissingOriginError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\n    git remote add origin <URL>\n") from None
    except GitTagExistsError as exc:
        _print_traceback(context)
        raise Error(f"{exc!s} Try:\n\nChoose another name or use '--force'\n") from None
    except CalledProcessError as exc:
        _print_traceback(context)
        cmd = shlex.join(exc.cmd)
        raise Error(f"{cmd!r} failed.") from None
    except Exception as exc:
        _print_traceback(context)
        raise Error(f"{exc!s}") from None


def _print_traceback(context: Context):
    if context.verbose > 1:  # pragma: no cover
        # pylint: disable=no-value-for-parameter
        lines = "".join(traceback.format_exc())
        context.secho(lines, fg="red", err=True)
