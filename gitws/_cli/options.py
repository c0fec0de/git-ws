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

"""Common Command Line Options."""
from pathlib import Path
from typing import Optional, Tuple

import click

from ..const import MANIFEST_PATH_DEFAULT


def projects_option():
    """Projects Option."""
    return click.option(
        "--project",
        "-P",
        "projects",
        multiple=True,
        type=click.Path(file_okay=False),
        help="Project path to operate on only. All by default. This option can be specified multiple times.",
    )


def manifest_option(initial=False):
    """Manifest Option."""
    if initial:
        help_ = f"Manifest file. '{MANIFEST_PATH_DEFAULT!s}' by default."
        default = MANIFEST_PATH_DEFAULT
    else:
        help_ = "Manifest file. Initial/Configuration settings by default."
        default = None
    return click.option(
        "--manifest", "-M", "manifest_path", type=click.Path(dir_okay=False), default=default, help=help_
    )


def update_option():
    """Update Option."""
    return click.option("--update", "-U", is_flag=True, help="Run 'git ws update' too.")


def force_option():
    """Force Option."""
    return click.option("--force", "-f", is_flag=True, help="Enfore operation.")


def group_filters_option(initial=False):
    """Group Filter Option."""
    if initial:
        help_ = """\
Group Filtering.
TODO: more details.
The setting becomes default for all successive runs.
"""
    else:
        help_ = """\
Group Filtering.
TODO: more details.
Initial clone/init filter settings by default.
"""
    return click.option("--group-filter", "-G", "group_filters", metavar="FILTER", multiple=True, help=help_)


def reverse_option():
    """Reverse Option."""
    help_ = "Operate in Reverse Order. Start with last dependency instead of main repository."
    return click.option("--reverse", "-R", "reverse", is_flag=True, help=help_)


def output_option():
    """Manifest Output Option."""
    return click.option(
        "--output",
        "-O",
        "output",
        type=click.Path(dir_okay=False),
        help="Write Manifest to file instead of STDOUT.",
    )


def path_option():
    """Path."""
    return click.argument("path", nargs=-1, type=click.UNPROCESSED)


def process_path(value) -> Optional[Path]:
    """Process `path_option`."""
    if value:
        if len(value) > 1:
            raise click.UsageError("more than one PATH specified")
        return Path(value[0])
    return None


def process_paths(paths) -> Tuple[Path, ...]:
    """Process `paths_argument`."""
    return tuple(Path(path) for path in paths)


def paths_argument():
    """Paths."""
    return click.argument("paths", nargs=-1, type=click.UNPROCESSED)


command_option = click.argument("command", nargs=-1, type=click.UNPROCESSED)


def process_command(command):
    """Process Command Argument."""
    if not command:
        raise click.UsageError("COMMAND is required")
    return command


command_options_option = click.argument("command_options", nargs=-1, type=click.UNPROCESSED)


def process_command_options(options):
    """Process options Argument."""
    return options or tuple()
