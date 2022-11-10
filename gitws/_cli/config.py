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

"""Configuration command."""

import json
from enum import Enum
from typing import Optional

import click

from gitws.appconfig import AppConfig, AppConfigLocation
from gitws.datamodel import AppConfigData
from gitws.exceptions import InvalidConfigurationOptionError, InvalidConfigurationValueError, UninitializedError
from gitws.workspace import Workspace

from .common import exceptionhandling, pass_context


class Format(str, Enum):
    """Controls printing of values."""

    TEXT = "text"
    """Print as plain text."""

    JSON = "json"
    """Print JSON formatted data."""


system_option = click.option(
    "--system",
    "target",
    flag_value=AppConfigLocation.SYSTEM.value,
    help="Operate on system wide configuration.",
)
"""Request working on system configuration only."""

user_option = click.option(
    "--user",
    "target",
    flag_value=AppConfigLocation.USER.value,
    help="Operate on user configuration.",
)
"""Request working on user configuration only."""

workspace_option = click.option(
    "--workspace",
    "target",
    flag_value=AppConfigLocation.WORKSPACE.value,
    help="Operate on workspace specific configuration.",
)
"""Request working on workspace configuration only."""

format_option = click.option(
    "-f",
    "--format",
    "format_",
    default=Format.TEXT.value,
    help="The format to use for showing values.",
    type=click.Choice(
        [Format.TEXT.value, Format.JSON.value],
    ),
)
"""Select the output format to use."""


# pylint: disable=unused-argument
@click.group()
def config(ctx=None, verbose=0):
    """Read and modify configuration values."""


@config.command()
@click.argument("option")
@system_option
@user_option
@workspace_option
@format_option
@pass_context
def get(context, option, target, format_):
    """
    Get the value of a configuration option.

    This prints the value of the specified option. If selected,
    the value of a specific configuration file will be read. Otherwise, the
    computed value of the configuration option is shown.

    The computed configuration value is created by
    merging the system, user and workspace configuration files in that order.
    On top, environment variables of the form GIT_WS_XXX (where XXX is the
    name of an option) can be used to override settings from the configuration
    files.

    Note that option also can be a user specific option from one of the
    configuration files that is not otherwise consumed by GitWS itself.
    """
    with exceptionhandling(context):
        config = AppConfig()
        if target is not None:
            options = config.load(target)
        else:
            options = config.options
        if format_ == Format.JSON:
            doc = {option: options.dict().get(option)}
            click.echo(json.dumps(doc))
        else:
            click.echo(options.dict().get(option))


@config.command(name="set")
@click.argument("option")
@click.argument("value")
@system_option
@user_option
@workspace_option
@click.option(
    "--ignore-unknown",
    "ignore_unknown",
    is_flag=True,
    help="Set the option, even if it is not known to the application. Note that this bypasses any type checking.",
)
@pass_context
def set_(context, option, value, target, ignore_unknown):
    """
    Set the configuration option to the given value.

    This sets an option to the given value. If no specific configuration file
    is selected, then this will update the workspace configuration if run
    from within a workspace. Otherwise, the user configuration will be updated.
    """
    with exceptionhandling(context):
        config = AppConfig()
        target = _select_default_location_if_none(target)
        with config.edit(target) as options:
            try:
                doc = AppConfigData(**{option: value})
                if not ignore_unknown:
                    schema = doc.schema()
                    props = schema.get("properties", {})
                    if option not in props:
                        raise InvalidConfigurationOptionError(option)
            except ValueError as value_error:
                raise InvalidConfigurationValueError(option, value) from value_error
            values = doc.dict(exclude_none=True)
            for key, val in values.items():
                setattr(options, key, val)


@config.command()
@click.argument("option")
@system_option
@user_option
@workspace_option
@pass_context
def delete(context, option, target):
    """
    Remove the option from the configuration.

    This removes the specified option from the selected configuration file. If
    no configuration file is explicitly selected, this will operate on the
    workspace configuration if ran from within a workspace. Otherwise, this
    will operate on the user configuration.
    """
    with exceptionhandling(context):
        target = _select_default_location_if_none(target)
        config = AppConfig()
        with config.edit(target) as options:
            setattr(options, option, None)


@config.command(name="list")
@format_option
@system_option
@user_option
@workspace_option
@pass_context
def _list(context, target, format_):
    """
    List all configuration options.

    This prints all configuration options. If selected, only the options from a
    specific configuration file will be shown. Otherwise, the computed list of
    configuration values is shown.

    The computed  configuration is created by
    merging the system, user and workspace configuration files in that order.
    On top, environment variables of the form GIT_WS_XXX (where XXX is the
    name of an option) can be used to override settings from the configuration
    files.

    Note that the listing might contain extra arguments if specified in one of
    the configuration files.
    """
    with exceptionhandling(context):
        config = AppConfig()
        if target is not None:
            options = config.load(target)
        else:
            options = config.options
        data = options.dict()
        if format_ == Format.TEXT:
            properties = options.schema().get("properties", {})
            for key, value in data.items():
                description = properties.get(key, {}).get("description", "Unknown/user option")
                click.echo(f"# {description}")
                if value is not None:
                    click.echo(f"{key} = {value}")
                else:
                    click.echo(key)
                click.echo()
        else:
            click.echo(json.dumps(data))


@config.command(name="files")
@format_option
@system_option
@user_option
@workspace_option
@pass_context
def files(context, target, format_):
    """
    Show the location of the configuration files.

    This prints the location of the configuration files used. By default, all
    paths are shown. The selection can be reduced by appropriate commands.
    """
    if target is None:
        locations = [AppConfigLocation.SYSTEM, AppConfigLocation.USER, AppConfigLocation.WORKSPACE]
    else:
        locations = [AppConfigLocation(target)]
    data = {}
    for location in locations:
        config = AppConfig()
        try:
            data[location.value] = str(config.get_config_file_path(location))
        except UninitializedError:
            data[location.value] = ""
    if format_ == Format.JSON.value:
        click.echo(json.dumps(data))
    else:
        for key, value in data.items():
            click.echo(f"{key}: {value}")


def _select_default_location_if_none(location: Optional[AppConfigLocation]) -> AppConfigLocation:
    """
    Select a default config location.

    This function returns the location as is if it is set. Otherwise, it checks
    if we are within  a Workspace. In this case, it returns AppConfigLocation.WORKSPACE.
    In any other case, AppConfigLocation.USER is returned.
    """
    if location is not None:
        return location
    try:
        Workspace.find_path()
        return AppConfigLocation.WORKSPACE
    except UninitializedError:
        return AppConfigLocation.USER
