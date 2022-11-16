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

"""Info Commands."""

from pathlib import Path

import click

from gitws import ManifestSpec, Remote

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
    Add Remote.
    """
    with exceptionhandling(context):
        manifest_path = Path(manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        remotes = list(manifest_spec.remotes)
        remotes.append(Remote(name=name, url_base=url_base))
        manifest_spec = manifest_spec.update(remotes=remotes)
        manifest_spec.save(manifest_path)


@remote.command(name="list")
@manifest_option(initial=True)
@pass_context
def list_(context, manifest_path):
    """
    List Remotes.
    """
    with exceptionhandling(context):
        manifest_path = Path(manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        for remote in manifest_spec.remotes:
            click.echo(f"{remote.name}: {remote.url_base}")


@remote.command()
@click.argument("name")
@manifest_option(initial=True)
@pass_context
def delete(context, name, manifest_path):
    """
    Delete Remote.
    """
    with exceptionhandling(context):
        manifest_path = Path(manifest_path)
        manifest_spec = ManifestSpec.load(manifest_path)
        remotes = list(manifest_spec.remotes)
        for idx, remote in enumerate(manifest_spec.remotes):
            if remote.name == name:
                break
        else:
            raise ValueError(f"Unknown dependency {name!r}")
        remotes.pop(idx)
        manifest_spec = manifest_spec.update(remotes=remotes)
        manifest_spec.save(manifest_path)
