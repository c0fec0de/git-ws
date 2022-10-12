"""Dependency Tree."""

from anytree import NodeMixin

from .datamodel import Manifest, ManifestSpec
from .exceptions import ManifestNotFoundError
from .workspace import Workspace


class Node(NodeMixin):
    """
    Dependency Tree Node.
    """

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent


def get_deptree(workspace: Workspace, manifest: Manifest) -> Node:
    """Calculate Dependency Tree."""
    main = workspace.info.main_path
    main_node = Node(main)
    _build(workspace, main_node, manifest)
    return main_node


def _build(workspace: Workspace, node: Node, manifest: Manifest):
    for project in manifest.dependencies:
        project_node = Node(project.path, parent=node)
        manifest_path = workspace.get_project_path(project) / project.manifest_path
        try:
            manifest_spec = ManifestSpec.load(manifest_path)
        except ManifestNotFoundError:
            continue
        manifest = Manifest.from_spec(manifest_spec)
        _build(workspace, project_node, manifest)
