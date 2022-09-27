"""
Manifest Handling.

:any:`Manifest`, :any:`ProjectSpec`, :any:`Remote` and :any:`Defaults` classes are pure data containers.
They do not implement any business logic on purpose.
:any:`Project` is a :any:`ProjectSpec` with applied :any:`Remote` and :any:`Defaults`.
"""

from pathlib import Path
from typing import Callable, List, Optional

import tomlkit
from pydantic import Field, root_validator

from ._basemodel import BaseModel
from ._url import urljoin
from .const import MANIFEST_PATH_DEFAULT
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


class Project(BaseModel):

    """
    ProjectSpec with resolved :any:`Defaults` and :any:`Remote`.

    Only `name`, `url`, `revisìon`, `path` will be set.

    Keyword Args:
        name (str): Unique name.
        path (str): ProjectSpec Filesystem Path. Relative to Workspace Root Directory.
        url (str): URL
        revision (str): Revision
    """

    name: str
    path: str
    url: Optional[str] = None
    revision: Optional[str] = None
    manifest_path: str = str(MANIFEST_PATH_DEFAULT)

    @staticmethod
    def from_spec(
        defaults: Defaults, remotes: List[Remote], spec: "ProjectSpec", refurl: Optional[str] = None
    ) -> "Project":
        """
        Create :any:`Project` from `defaults`, `remotes` and `spec`.

        Args:
            defaults (Defaults): Default settings if not given by `spec`.
            remotes (List[Remote]): Remotes
            spec (ProjectSpec): Base project to be resolved.
        """
        url = spec.url
        if not url:
            # URL assembly
            project_remote = spec.remote or defaults.remote
            if project_remote:
                project_sub_url = spec.sub_url or spec.name
                for remote in remotes:
                    if remote.name == project_remote:
                        url = f"{remote.url_base}/{project_sub_url}"
                        break
                else:
                    raise ValueError(f"Unknown remote {spec.remote} for project {spec.name}")

        # Resolve relative URLs.
        url = urljoin(refurl, url)
        return Project(
            name=spec.name,
            path=spec.path or spec.name,
            url=url,
            revision=spec.revision or defaults.revision,
            manifest_path=spec.manifest_path,
        )


class ProjectSpec(BaseModel, allow_population_by_field_name=True):
    """
    ProjectSpec.

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
        path (str): ProjectSpec Filesystem Path. Relative to Workspace Root Directory.
        manifest_path (str): Path to manifest. Relative to ProjectSpec Filesystem Path. `anyrepo.toml` by default.
    """

    name: str
    remote: Optional[str] = None
    sub_url: Optional[str] = Field(None, alias="sub-url")
    url: Optional[str] = None
    revision: Optional[str] = None
    path: Optional[str] = None
    manifest_path: str = str(MANIFEST_PATH_DEFAULT)

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

    defaults: Defaults = Defaults()
    remotes: List[Remote] = []
    dependencies: List[ProjectSpec] = []

    @classmethod
    def load(cls, path: Path, default: Optional["Manifest"] = None) -> "Manifest":
        """
        Load :any:`Manifest` from `path`.

        The file referenced by `path` should be a YAML file according to the
        manifest scheme.
        """
        try:
            content = path.read_text()
        except FileNotFoundError:
            if default:
                return default
            raise ManifestNotFoundError(path) from None
        doc = tomlkit.parse(content)
        data = dict(doc)
        return cls(**data)

    def dump(self) -> str:
        """
        Return :any:`Manifest` as string.
        """
        doc = tomlkit.document()
        for key, value in self.dict(by_alias=True, exclude_none=True, exclude_defaults=True).items():
            if value:
                doc[key] = value
        return tomlkit.dumps(doc)

    def save(self, path: Path):
        """
        Save :any:`Manifest` at `path`.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.dump())


def create_project_filter(project_paths: Optional[List[Path]] = None) -> Callable[[ProjectSpec], bool]:
    """Create filter function."""
    if project_paths:
        initialized_project_paths: List[Path] = project_paths
        return lambda project: project.path in initialized_project_paths
    return lambda _: True
