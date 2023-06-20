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

from gitws import ManifestSpec, ProjectSpec
from gitws._util import as_dict

from .common import exceptionhandling, pass_context
from .options import manifest_option


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
        manifest_spec = ManifestSpec.load(manifest_path)
        dependencies = list(manifest_spec.dependencies)
        dependencies.append(
            ProjectSpec(name=name).update_fromstr(
                {
                    "remote": remote,
                    "sub-url": sub_url,
                    "url": url,
                    "revision": revision,
                    "path": path,
                    "manifest-path": dep_manifest_path,
                    "groups": groups,
                    "with-groups": with_groups,
                    "submodules": submodules,
                }
            )
        )
        manifest_spec = manifest_spec.update(dependencies=dependencies)
        manifest_spec.save(manifest_path)


_DEP_ATTRIBUTES = tuple(
    (item for item in ProjectSpec(name="dummy").dict(by_alias=True) if item not in ("linkfiles", "copyfiles"))
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
        manifest_spec = ManifestSpec.load(manifest_path)
        dependencies = list(manifest_spec.dependencies)
        for idx, dependency in enumerate(dependencies):
            if dependency.name == dep:
                break
        else:
            raise ValueError(f"Unknown dependency {dep!r}")
        dependencies[idx] = dependencies[idx].update_fromstr({attribute: value if value else None})
        manifest_spec = manifest_spec.update(dependencies=dependencies)
        manifest_spec.save(manifest_path)


@dep.command(name="list")
@manifest_option(initial=True)
@pass_context
def list_(context, manifest_path):
    """
    List Dependencies.
    """
    with exceptionhandling(context):
        manifest_spec = ManifestSpec.load(manifest_path)
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
        manifest_spec = ManifestSpec.load(manifest_path)
        dependencies = list(manifest_spec.dependencies)
        for idx, dep in enumerate(manifest_spec.dependencies):
            if dep.name == name:
                break
        else:
            raise ValueError(f"Unknown dependency {name!r}")
        dependencies.pop(idx)
        manifest_spec = manifest_spec.update(dependencies=dependencies)
        manifest_spec.save(manifest_path)
