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

"""Dependency Commands."""
import click
import tomlkit

from gitws import ProjectSpec
from gitws._cli.common import exceptionhandling, pass_context
from gitws._cli.dep.update import update
from gitws._cli.options import manifest_option
from gitws._manifestformatmanager import get_manifest_format_manager
from gitws._util import as_dict


@click.group()
def dep():
    """
    Manage Dependencies.
    """


@dep.command()
@click.argument("name")
@click.option("--remote", help="Remote")
@click.option("--sub-url", help="Sub-URL")
@click.option("--url", help="URL")
@click.option("--revision", help="Revision")
@click.option("--path", help="Path")
@click.option("--dep-manifest-path", help="Dependency Manifest Path")
@click.option("--groups", help="Groups")
@click.option("--with-groups", help="With Groups")
@click.option("--submodules", help="Submodules")
@manifest_option(initial=True)
@pass_context
def add(
    context,
    name,
    manifest_path,
    remote=None,
    sub_url=None,
    url=None,
    revision=None,
    path=None,
    dep_manifest_path=None,
    groups=None,
    with_groups=None,
    submodules=None,
):
    """
    Add Dependency NAME.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            dependencies = list(manifest_spec.dependencies)
            dependencies.append(
                ProjectSpec(name=name).model_copy_fromstr(
                    {
                        "remote": remote,
                        "sub_url": sub_url,
                        "url": url,
                        "revision": revision,
                        "path": path,
                        "manifest_path": dep_manifest_path,
                        "groups": groups,
                        "with_groups": with_groups,
                        "submodules": submodules,
                    }
                )
            )
            manifest_spec = manifest_spec.model_copy(update={"dependencies": tuple(dependencies)})
            handler.save(manifest_spec)


_DEP_ATTRIBUTES = tuple(
    item for item in ProjectSpec(name="dummy").model_dump(by_alias=True) if item not in ("linkfiles", "copyfiles")
)


@dep.command(name="set")
@manifest_option(initial=True)
@click.argument("dep")
@click.argument("attribute", type=click.Choice(_DEP_ATTRIBUTES))
@click.argument("value")
@pass_context
def set_(context, manifest_path, dep, attribute, value):
    """
    Set ATTRIBUTE For Dependency DEP to VALUE.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            dependencies = list(manifest_spec.dependencies)
            for idx, dependency in enumerate(dependencies):
                if dependency.name == dep:
                    dependencies[idx] = dependencies[idx].model_copy_fromstr({attribute: value})
                    break
            else:
                raise ValueError(f"Unknown dependency {dep!r}")
            manifest_spec = manifest_spec.model_copy(update={"dependencies": tuple(dependencies)})
            handler.save(manifest_spec)


@dep.command(name="list")
@manifest_option(initial=True)
@pass_context
def list_(context, manifest_path):
    """
    List Dependencies.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            doc = tomlkit.document()
            doc.add("dependencies", as_dict(manifest_spec)["dependencies"])
        click.echo(tomlkit.dumps(doc))


@dep.command()
@click.argument("name")
@manifest_option(initial=True)
@pass_context
def delete(context, name, manifest_path):
    """
    Delete Dependency NAME.
    """
    with exceptionhandling(context):
        with get_manifest_format_manager().handle(manifest_path) as handler:
            manifest_spec = handler.load()
            dependencies = list(manifest_spec.dependencies)
            for idx, dep in enumerate(manifest_spec.dependencies):
                if dep.name == name:
                    dependencies.pop(idx)
                    break
            else:
                raise ValueError(f"Unknown dependency {name!r}")
            manifest_spec = manifest_spec.model_copy(update={"dependencies": tuple(dependencies)})
            handler.save(manifest_spec)


dep.add_command(update)
