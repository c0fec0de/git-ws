"""Dependency Tree."""

from typing import List

from anytree import NodeMixin
from anytree.exporter import DotExporter

from .datamodel import Manifest, ManifestSpec, Project
from .exceptions import ManifestNotFoundError
from .workspace import Workspace


class Node(NodeMixin):
    """
    Dependency Tree Node.
    """

    def __init__(self, project, is_primary=False, parent=None):
        self.project = project
        self.is_primary = is_primary
        self.parent = parent


def get_deptree(workspace: Workspace, manifest: Manifest) -> Node:
    """Calculate Dependency Tree."""
    main = str(workspace.info.main_path)
    main_node = Node(Project(name=main, path=main))
    primaries: List[str] = []
    _build(primaries, workspace, main_node, manifest)
    return main_node


def _build(primaries: List, workspace: Workspace, node: Node, manifest: Manifest):
    for project in manifest.dependencies:
        is_primary = project.path not in primaries
        if is_primary:
            primaries.append(project.path)
        project_node = Node(project, is_primary=is_primary, parent=node)
        manifest_path = workspace.get_project_path(project) / project.manifest_path
        try:
            manifest_spec = ManifestSpec.load(manifest_path)
        except ManifestNotFoundError:
            continue
        manifest = Manifest.from_spec(manifest_spec)
        _build(primaries, workspace, project_node, manifest)


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
        groups = ",".join(group.info for group in project.groups)
        if project.groups:
            labels.append(f"({groups})")
        if labels:
            labelstr = " ".join(labels)
            attrs.append(f'label="{labelstr}"')
        if attrs:
            return ";".join(attrs)
        return None

    def __init__(self, node: Node):
        super().__init__(node, nodenamefunc=self._nodename, edgeattrfunc=self._edgeattr)
