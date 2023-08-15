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
        "--manifest",
        "-M",
        "manifest_path",
        type=click.Path(dir_okay=False, path_type=Path),
        default=default,
        help=help_,
    )


def update_option():
    """Update Option."""
    return click.option("--update", "-U", is_flag=True, help="Run 'git ws update' too.")


def force_option():
    """Force Option."""
    return click.option("--force", "-f", is_flag=True, help="Enfore operation.")


def group_filters_option(initial=False):
    """Group Filter Option."""
    help_ = """\
Group Filtering.
All groups from the main manifest are enabled by default,
unless deactivated by the `[group-filters]` section or this option.
This option has the highest precedence and can be specified multiple times.
"""
    if initial:
        help_ = f"{help_}The setting becomes default for all successive runs."
    else:
        help_ = f"{help_}Initial clone/init filter settings are used by default."
    return click.option("--group-filter", "-G", "group_filters", metavar="FILTER", multiple=True, help=help_)


def unshallow_option():
    """Convert To A Complete Repository."""
    return click.option("--unshallow", is_flag=True, help="convert to a complete repository")


def reverse_option():
    """Reverse Option."""
    help_ = "Operate in Reverse Order. Start with last dependency instead of main repository."
    return click.option("--reverse", "-R", "reverse", is_flag=True, help=help_)


def on_branch_option():
    """On Branch Option."""
    help_ = "Limit operation to clones on branches only. Detached HEAD clones (on tag or SHA) are ignored."
    return click.option("--on-branch", "-b", "on_branch", is_flag=True, help=help_)


def output_option():
    """Manifest Output Option."""
    return click.option(
        "--output",
        "-O",
        "output",
        type=click.Path(dir_okay=False, path_type=Path),
        help="Write Manifest to file instead of STDOUT.",
    )


def ws_path_option(nomain: bool = False):
    """Workspace Path Option."""
    if nomain:
        descr = "Workspace Path. Parent directory of main project by default."
    else:
        descr = "Workspace Path. Parent directory of main project or current working directory by default."
    return click.option(
        "--ws-path",
        "-w",
        "ws_path",
        type=click.Path(file_okay=False, path_type=Path),
        help=descr,
    )


def main_path_option():
    """Main Repository Path."""
    return click.argument("main_path", nargs=-1, type=click.UNPROCESSED)


def depth_option():
    """Depth Option."""
    return click.option("--depth", type=int, help="Create clones shallow of that depth.")


def process_main_path(value) -> Optional[Path]:
    """Process ``path_option``."""
    if value:
        if len(value) > 1:
            raise click.UsageError("more than one PATH specified")
        return Path(value[0])
    return None


def process_paths(paths) -> Tuple[Path, ...]:
    """Process ``paths_argument``."""
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
