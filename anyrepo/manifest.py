"""
Manifest Handling.

:any:`Manifest`, :any:`Project`, :any:`Remote` and :any:`Defaults` classes are pure data containers.
They do not implement any business logic on purpose.
:any:`ResolvedProject` is a :any:`Project` with applied :any:`Remote` and :any:`Defaults`.
"""

from pathlib import Path
from typing import Callable, List, Optional

import tomlkit
from pydantic import BaseModel, Field, root_validator

from .exceptions import ManifestNotFoundError


class Remote(BaseModel, allow_population_by_field_name=True):
    """
    Remote Alias.

    Args:
        name: Remote Name

    Keyword Args:
        url_base: Base URL. Optional.
    """

    name: str
    url_base: Optional[str] = Field(None, alias="url-base")


class Defaults(BaseModel):
    """
    Default Values.

    These default values are used, if the project does not specify them.

    Keyword Args:
        remote: Remote Name
        revision: Revision
    """

    remote: Optional[str] = None
    revision: Optional[str] = None


class Project(BaseModel, allow_population_by_field_name=True):
    """
    Project.

    A project specifies the reference to a repository.

    Some parameters are restricted:

    * `remote` and `url` are mutually exclusive.
    * `url` and `sub-url` are likewise mutually exclusive
    * `sub-url` requires a `remote`.

    Keyword Args:
        name (str): Unique name.
        remote (str): Remote Alias
        sub_url (str): URL relative to :any:`Remote.url_base`.
        url (str): URL
        revision (str): Revision
        path (str): Project Filesystem Path. Relative to Workspace Root Directory.
    """

    name: str
    remote: Optional[str] = None
    sub_url: Optional[str] = Field(None, alias="sub-url")
    url: Optional[str] = None
    revision: Optional[str] = None
    path: Optional[str] = None

    @root_validator(allow_reuse=True)
    def _remote_or_url(cls, values):
        # pylint: disable=no-self-argument,no-self-use
        remote = values.get("remote", None)
        sub_url = values.get("sub_url", None)
        url = values.get("url", None)
        if remote and url:
            raise ValueError("'remote' and 'url' are mutually exclusive")
        if url and sub_url:
            raise ValueError("'url' and 'sub-url' are mutually exclusive")
        if sub_url and not remote:
            raise ValueError("'sub-url' requires 'remote'")
        return values


class Manifest(BaseModel, allow_population_by_field_name=True):

    """
    Manifest.

    A manifest describes the actual project and its dependencies.

    Keyword Args:
        path: Checkout path.
        defaults: Default settings.
        remotes: Remote Aliases
        dependencies: Dependency Projects.
    """

    path: Optional[str] = None
    defaults: Defaults = Defaults()
    remotes: List[Remote] = []
    dependencies: List[Project] = []

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        """
        Load :any:`Manifest` from `path`.

        The file referenced by `path` should be a YAML file according to the
        manifest scheme.
        """
        try:
            content = path.read_text()
        except FileNotFoundError:
            raise ManifestNotFoundError(path) from None
        doc = tomlkit.parse(content)
        data = dict(doc)
        return cls(**data)

    def save(self, path: Path):
        """
        Save :any:`Manifest` at `path`.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()
        for key, value in self.dict(by_alias=True, exclude_none=True).items():
            if value:
                doc[key] = value
        path.write_text(tomlkit.dumps(doc))


class ResolvedProject(Project):

    """
    Project with resolved :any:`Defaults` and :any:`Remote`.

    Only `name`, `url`, `revisìon`, `path` will be set.

    Keyword Args:
        name (str): Unique name.
        url (str): URL
        revision (str): Revision
        path (str): Project Filesystem Path. Relative to Workspace Root Directory.
        manifest (Manifest): Project Manifest.
    """

    name: str
    path: str
    url: Optional[str] = None
    revision: Optional[str] = None
    manifest: Optional[Manifest] = None

    @staticmethod
    def from_project(defaults: Defaults, remotes: List[Remote], project: Project) -> "ResolvedProject":
        """
        Create :any:`ResolvedProject` from `defaults`, `remotes` and `project`.

        Args:
            defaults (Defaults): Default settings if not given by `project`.
            remotes (List[Remote]): Remotes
            project (Project): Base project to be resolved.
        """
        url = project.url
        if not url:
            # URL assembly
            project_remote = project.remote or defaults.remote
            if project_remote:
                project_sub_url = project.sub_url or project.name
                for remote in remotes:
                    if remote.name == project_remote:
                        url = f"{remote.url_base}/{project_sub_url}"
                        break
                else:
                    raise ValueError(f"Unknown remote {project.remote} for project {project.name}")
        return ResolvedProject(
            name=project.name,
            path=project.path or project.name,
            url=url,
            revision=project.revision or defaults.revision,
        )


def create_project_filter(project_paths: Optional[List[Path]] = None) -> Callable[[Project], bool]:
    """Create filter function."""
    if project_paths:
        initialized_project_paths: List[Path] = project_paths
        return lambda project: project.path in initialized_project_paths
    return lambda _: True
