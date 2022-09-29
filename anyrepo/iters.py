"""ManifestSpec and Project Iterators."""
import logging
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from ._git import Git
from .datamodel import Manifest, ManifestSpec, Project
from .filters import default_filter
from .types import ProjectFilter
from .workspace import Workspace

_LOGGER = logging.getLogger("anyrepo")
_MANIFEST_DEFAULT = ManifestSpec()


class ManifestIter:
    """Iterator to resolve the manifest dependencies."""

    # pylint: disable=too-few-public-methods
    def __init__(self, workspace: Workspace, manifest_path: Path, filter_: Optional[ProjectFilter] = None):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.filter_: ProjectFilter = filter_ or default_filter
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Manifest, None, None]:
        yield from self.__iter(self.workspace.main_path, self.manifest_path)

    def __iter(self, project_path: Path, manifest_path: Path) -> Generator[Manifest, None, None]:
        deps: List[Tuple[Path, Path]] = []
        done: List[str] = self.__done
        filter_ = self.filter_

        manifest_spec = ManifestSpec.load(manifest_path)
        manifest = Manifest.from_spec(manifest_spec, path=str(manifest_path))
        _LOGGER.debug("%r", manifest)
        yield manifest

        for dep_project in manifest.dependencies:
            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            if not filter_(dep_project):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            _LOGGER.debug("%r", dep_project)
            dep_project_path = self.workspace.path / dep_project.path

            # Recursive
            dep_manifest_path = dep_project_path / dep_project.manifest_path
            if dep_manifest_path.exists():
                deps.append((dep_project_path, dep_manifest_path))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_project_path, dep_manifest_path in deps:
            yield from self.__iter(dep_project_path, dep_manifest_path)


class ProjectIter:
    """Iterator to resolve the project dependencies."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        workspace: Workspace,
        manifest_path: Path,
        filter_: Optional[ProjectFilter] = None,
        skip_main: bool = False,
        resolve_url: bool = False,
    ):
        self.workspace: Workspace = workspace
        self.manifest_path: Path = manifest_path
        self.filter_: ProjectFilter = filter_ or default_filter
        self.skip_main: bool = skip_main
        self.resolve_url: bool = resolve_url
        self.__done: List[str] = []

    def __iter__(self) -> Generator[Project, None, None]:
        if not self.skip_main:
            workspace = self.workspace
            info = workspace.info
            project = Project(name=info.main_path.name, path=str(info.main_path))
            if self.filter_(project):
                yield project
        manifest = ManifestSpec.load(self.manifest_path, default=ManifestSpec())
        yield from self.__iter(self.workspace.main_path, manifest)

    def __iter(self, project_path: Path, manifest: ManifestSpec) -> Generator[Project, None, None]:
        deps: List[Tuple[Path, ManifestSpec]] = []
        refurl: Optional[str] = None
        filter_ = self.filter_
        done: List[str] = self.__done
        if self.resolve_url:
            git = Git(project_path)
            assert git.is_cloned()
            refurl = git.get_url()

        _LOGGER.debug("%r", manifest)

        for spec in manifest.dependencies:
            dep_project = Project.from_spec(manifest, spec, refurl=refurl)

            # Update every path just once
            if dep_project.path in done:
                _LOGGER.debug("DUPLICATE %r", dep_project)
                continue
            done.append(dep_project.path)

            dep_project_path = self.workspace.path / dep_project.path
            if not filter_(dep_project):
                _LOGGER.debug("FILTERED OUT %r", dep_project)
                continue

            _LOGGER.debug("%r", dep_project)
            yield dep_project

            # Recursive
            dep_manifest_path = dep_project_path / dep_project.manifest_path
            dep_manifest = ManifestSpec.load(dep_manifest_path, default=_MANIFEST_DEFAULT)
            if dep_manifest != _MANIFEST_DEFAULT:
                deps.append((dep_project_path, dep_manifest))

        # We resolve all dependencies in a second iteration to prioritize the manifest
        for dep_project_path, dep_manifest in deps:
            yield from self.__iter(dep_project_path, dep_manifest)
