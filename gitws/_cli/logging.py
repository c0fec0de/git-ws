# Copyright 2022-2023 c0fec0de
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

"""Logging."""
import logging

import click

_LOGLEVELMAP = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


class LogHandler(logging.Handler):
    """Logging Handler."""

    def __init__(self):
        super().__init__()
        self.has_errors = False

    def emit(self, record):
        """Emit Message."""
        if record.levelno >= logging.ERROR:
            self.has_errors = True
        click.echo(self.format(record), err=record.levelno >= logging.WARNING)


class LogFormatter(logging.Formatter):
    """Log Formatter."""

    levelsettings = {  # noqa: RUF012
        logging.WARNING: {"fg": "yellow", "bold": True},
        logging.ERROR: {"fg": "red", "bold": True},
    }
    leveldefault = {"bold": True, "dim": True}  # noqa: RUF012
    msgsettings = {  # noqa: RUF012
        logging.DEBUG: {"dim": True, "fg": "cyan"},
        logging.INFO: {"dim": True, "fg": "blue"},
        logging.WARNING: {"fg": "yellow"},
        logging.ERROR: {"fg": "red"},
    }
    msgdefault = {"fg": "blue", "dim": True}  # noqa: RUF012

    def __init__(self, color: bool):
        super().__init__()
        self.color: bool = color

    def format(self, record):
        """Format Message."""
        msg = record.getMessage()
        if self.color:
            levelsetting = self.levelsettings.get(record.levelno, self.leveldefault)
            msgsetting = self.msgsettings.get(record.levelno, self.msgdefault)
            prefix = click.style(f"{record.levelname}:".ljust(8), **levelsetting)
            lines = [click.style(line, **msgsetting) for line in msg.splitlines()]
        else:
            prefix = f"{record.levelname}:".ljust(8)
            lines = msg.splitlines()

        return "\n".join(f"{prefix} {line}" for line in lines)


def setup_logging(color: bool, verbose: int) -> LogHandler:
    """Create And Setup Logging Handler."""
    handler = LogHandler()
    handler.formatter = LogFormatter(color)
    logger = logging.getLogger()
    level = _LOGLEVELMAP.get(verbose, logging.DEBUG)
    logger.setLevel(level)
    logger.handlers = [handler]
    return handler
