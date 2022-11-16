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

"""Manifest Commands."""
from pathlib import Path

import click

from gitws import GitWS, ManifestSpec

from .common import COLOR_INFO, exceptionhandling, pass_context
from .options import group_filters_option, manifest_option, output_option


@click.group()
def manifest():
    """
    Manifest Information.
    """


@manifest.command()
@manifest_option()
@group_filters_option()
@output_option()
@pass_context
def resolve(context, manifest_path=None, group_filters=None, output=None):
    """
    Print The Manifest With All Projects And All Their Dependencies.

    The output is a single manifest file with all dependencies and their dependencies.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        manifest = gws.get_manifest_spec(resolve=True)
        if output:
            manifest.save(Path(output))
        else:
            click.echo(manifest.dump())


@manifest.command()
@manifest_option()
@group_filters_option()
@output_option()
@pass_context
def freeze(context, manifest_path=None, group_filters=None, output=None):
    """
    Print The Resolved Manifest With SHAs For All Project Revisions.

    The output is identical to resolve, a single manifest file with all dependencies and their dependencies.
    Revisions are replaced by the actual SHAs.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        manifest_spec = gws.get_manifest_spec(freeze=True, resolve=True)
        if output:
            manifest_spec.save(Path(output))
        else:
            click.echo(manifest_spec.dump())


@manifest.command()
@manifest_option()
@pass_context
def validate(context, manifest_path=None):
    """
    Validate The Current Manifest, Exiting With An Error On Issues.
    """
    with exceptionhandling(context):
        GitWS.from_path(manifest_path=manifest_path)


@manifest.command()
@manifest_option()
@group_filters_option()
@pass_context
def path(context, manifest_path=None, group_filters=None):
    """
    Print Path to Main Manifest File.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        manifest = next(gws.manifests())
        click.echo(str(manifest.path))


@manifest.command()
@manifest_option()
@group_filters_option()
@pass_context
def paths(context, manifest_path=None, group_filters=None):
    """
    Print Paths to ALL Manifest Files.
    """
    with exceptionhandling(context):
        gws = GitWS.from_path(manifest_path=manifest_path, group_filters=group_filters)
        for manifest in gws.manifests():
            click.echo(str(manifest.path))


@manifest.command()
@manifest_option(initial=True)
@pass_context
def create(context, manifest_path):
    """Create Manifest."""
    with exceptionhandling(context):
        path = GitWS.create_manifest(Path(manifest_path))
        click.secho(f"Manifest {str(path)!r} created.", fg=COLOR_INFO)


@manifest.command()
@manifest_option(initial=True)
@pass_context
def upgrade(context, manifest_path):
    """
    Update Manifest To Latest Version.

    User data is kept.
    User comments are removed.
    Comments are updated to the latest documentation.
    """
    with exceptionhandling(context):
        ManifestSpec.upgrade(Path(manifest_path))
        click.secho(f"Manifest {str(manifest_path)!r} upgraded.", fg=COLOR_INFO)
