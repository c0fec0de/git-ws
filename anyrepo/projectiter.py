"""The one-and-only Iterator."""
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from ._git import Git
from .manifest import Manifest, Project
from .workspace import Workspace

_LOGGER = logging.getLogger(__name__)
_MANIFEST_DEFAULT = Manifest()


class ProjectIter:
    """The one-and-only Iterator to resolve the manifest dependencies."""

    # pylint: disable=too-few-public-methods

    def __init__(self, workspace: Workspace, manifest: Manifest, skip_main: bool = False, resolve_url: bool = False):
        self.workspace = workspace
        self.manifest = manifest
        self.skip_main = skip_main
        self.resolve_url = resolve_url
        self.__done: List[str] = []

    def __iter__(self):
        if not self.skip_main:
            workspace = self.workspace
            info = workspace.info
            yield Project(
                name=info.main_path.name,
                path=str(info.main_path),
            )
        yield from self.__iter(self.workspace.main_path, self.manifest)

    def __iter(self, project_path: Path, manifest: Manifest):
        deps: List[Tuple[Path, Manifest]] = []
        refurl: Optional[str] = None
        done: List[str] = self.__done
        if self.resolve_url:
            git = Git(project_path)
            assert git.is_cloned()
            refurl = git.get_url()

        _LOGGER.debug("%r", manifest)

        for dep in manifest.dependencies:
            rdep = Project.from_spec(manifest.defaults, manifest.remotes, dep, refurl=refurl)

            # Update every path just once
            if rdep.path in done:
                _LOGGER.debug("DUPLICATE %r", rdep)
                continue
            _LOGGER.debug("%r", rdep)
            done.append(rdep.path)

            dep_project_path = self.workspace.path / rdep.path
            yield rdep

            # Recursive
            dep_manifest_path = dep_project_path / rdep.manifest_path
            dep_manifest = Manifest.load(dep_manifest_path, default=_MANIFEST_DEFAULT)
            if dep_manifest != _MANIFEST_DEFAULT:
                deps.append((dep_project_path, dep_manifest))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_project_path, dep_manifest in deps:
            yield from self.__iter(dep_project_path, dep_manifest)
