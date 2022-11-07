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

"""Dependency Tree."""

import logging
from typing import List, Tuple

from anytree import NodeMixin
from anytree.exporter import DotExporter

from .datamodel import Manifest, ManifestSpec, Project
from .exceptions import ManifestNotFoundError
from .workspace import Workspace

_LOGGER = logging.getLogger("git-ws")


class DepNode(NodeMixin):
    """
    Dependency Tree Node.
    """

    def __init__(self, project, is_primary=False, parent=None):
        self.project = project
        self.is_primary = is_primary
        self.parent = parent


def get_deptree(workspace: Workspace, manifest: Manifest, primary: bool = False) -> DepNode:
    """Calculate Dependency Tree."""
    main = str(workspace.info.main_path)
    main_node = DepNode(Project(name=main, path=main), is_primary=True)
    primaries: List[str] = []
    edges: List[Tuple[str, str]] = []
    _build(primaries, edges, workspace, main_node, manifest, primary=primary)
    return main_node


def _build(
    primaries: List, edges: List, workspace: Workspace, node: DepNode, manifest: Manifest, primary: bool = False
):
    _LOGGER.debug("get_deptree(primaries=%r, path=%r)", primaries, node.project.path)
    for project in manifest.dependencies:
        edge = (node.project.path, project.path)
        if edge in edges:
            continue
        edges.append(edge)
        is_primary = project.path not in primaries
        if is_primary:
            primaries.append(project.path)
        elif primary:
            continue
        project_node = DepNode(project, is_primary=is_primary, parent=node)
        manifest_path = workspace.get_project_path(project) / project.manifest_path
        try:
            manifest_spec = ManifestSpec.load(manifest_path)
        except ManifestNotFoundError:
            continue
        manifest = Manifest.from_spec(manifest_spec)
        if is_primary:
            _build(primaries, edges, workspace, project_node, manifest, primary=primary)


class DepDotExporter(DotExporter):
    """DOT Exporter."""

    @staticmethod
    def _nodename(node):
        """Node Name."""
        return node.project.path

    @staticmethod
    def _edgeattr(node, child):
        """Edge Attributes."""
        # pylint:disable=unused-argument
        project = child.project
        attrs = []
        if not child.is_primary:
            attrs.append('style="dashed"')
        labels = []
        if project.revision:
            labels.append(project.revision)
        groups = ",".join(project.groups)
        if project.groups:
            labels.append(f"({groups})")
        if labels:
            labelstr = " ".join(labels)
            attrs.append(f'label="{labelstr}"')
        if attrs:
            return ";".join(attrs)
        return None

    def __init__(self, node: DepNode):
        super().__init__(node, nodenamefunc=self._nodename, edgeattrfunc=self._edgeattr)
