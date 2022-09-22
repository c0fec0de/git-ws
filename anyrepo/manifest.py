"""
Manifest Data Container.

The :any:`Manifest` and :any:`Project` classes are pure data container.
They do not implement any business logic.
"""

from pathlib import Path
from typing import Callable, List, Optional

from pydantic import BaseModel, Field, root_validator


class Remote(BaseModel, allow_population_by_field_name=True):
    """
    Remote Alias.

    :param name: Remote Name
    :param url_base: Base URL. Optional.
    """

    name: str
    url_base: Optional[str] = Field(None, alias="url-base")


class Defaults(BaseModel):
    """
    Default Values.

    These default values are used, if the project does not specify it.

    :param remote: Remote Name
    :param revision: Revision
    """

    remote: Optional[str] = None
    revision: Optional[str] = None


class Project(BaseModel, allow_population_by_field_name=True):
    """
    Project.

    A project specifies the reference to a repository.
    `remote` and `url` are mutually exclusive.
    `url` and `sub-url` are likewise mutually exclusive, but `sub-url` requires a `remote`.

    :param name (str): Unique name.
    :param remote (str): Remote Alias
    :param sub_url (str): URL relative to remote url_base.
    :param url (str): URL
    :param revision (str): Revision
    :param path (str): Project Filesystem Path. Relative to Workspace Directory.
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


class Manifest(BaseModel):

    """
    Manifest.

    :param path (Path): Path to the manifest file. Relative to git top directory.
    :param defaults (Defaults): Default settings.
    :param remotes (List[Remote]): Remote Aliases
    :param projects (List[Project]): Projects.
    """

    path: Optional[Path] = None
    defaults: Defaults = Defaults()
    remotes: List[Remote] = []
    projects: List[Project] = []


class ResolvedProject(Project):

    """
    Project with resolved `defaults` and `remotes`.

    Only `name`, `url`, `revisìon`, `path` will be set.
    """

    manifest: Optional[Manifest] = None

    @staticmethod
    def from_project(manifest: Manifest, project: Project) -> "ResolvedProject":
        """
        Create :any:`ResolvedProject` from `manifest` and `project`.
        """
        url = project.url
        if not url:
            # URL assembly
            project_remote = project.remote or manifest.defaults.remote
            project_sub_url = project.sub_url or project.name
            for remote in manifest.remotes:
                if remote.name == project_remote:
                    url = f"{remote.url_base}/{project_sub_url}"
                    break
            else:
                raise ValueError(f"Unknown remote {project.remote} for project {project.name}")
        return ResolvedProject(
            name=project.name,
            url=url,
            revision=project.revision or manifest.defaults.revision,
            path=project.path or project.name,
        )


def create_project_filter(project_paths: Optional[List[Path]] = None) -> Callable[[Project], bool]:
    """Create filter function."""
    if project_paths:
        initialized_project_paths: List[Path] = project_paths
        return lambda project: project.path in initialized_project_paths
    return lambda _: True
