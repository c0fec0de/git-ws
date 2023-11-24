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

"""Info Commands."""


import click

from gitws import Remote
from gitws._manifestformatmanager import get_manifest_format_manager

from .common import exceptionhandling, pass_context
from .options import manifest_option


@click.group()
def remote():
    """
    Manage Remotes.
    """


@remote.command()
@click.argument("name")
@click.argument("url_base")
@manifest_option(initial=True)
@pass_context
def add(context, name, url_base, manifest_path):
    """
    Add Remote NAME with URL_BASE.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            remotes = list(manifest_spec.remotes)
            remotes.append(Remote(name=name, url_base=url_base))
            manifest_spec = manifest_spec.model_copy(update={"remotes": tuple(remotes)})
            handler.save(manifest_spec)


@remote.command(name="list")
@manifest_option(initial=True)
@pass_context
def list_(context, manifest_path):
    """
    List Remotes.
    """
    with exceptionhandling(context):
        manifest_spec = get_manifest_format_manager().load(manifest_path)
        for remote in manifest_spec.remotes:
            click.echo(f"{remote.name}: {remote.url_base}")


@remote.command()
@click.argument("name")
@manifest_option(initial=True)
@pass_context
def delete(context, name, manifest_path):
    """
    Delete Remote NAME.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            remotes = list(manifest_spec.remotes)
            for idx, remote in enumerate(manifest_spec.remotes):
                if remote.name == name:
                    remotes.pop(idx)
                    break
            else:
                raise ValueError(f"Unknown dependency {name!r}")
            manifest_spec = manifest_spec.model_copy(update={"remotes": tuple(remotes)})
            handler.save(manifest_spec)
