"""
Manifest Data Container.

The :any:`Manifest` and :any:`Project` classes are pure data container.
They do not implement any business logic.
"""

from pathlib import Path
from typing import Callable, List, Optional

from pydantic import BaseModel, Field, root_validator

from ._url import urljoin


class Remote(BaseModel):
    """
    Remote Alias

    :param name: Remote Name
    :param urlbase: Base URL. Optional.
    """

    name: str
    urlbase: Optional[str] = None


class Defaults(BaseModel):
    """
    Default Values

    :param remote: Remote Name
    :param revision: Revision
    """

    remote: Optional[str] = None
    revision: Optional[str] = None


class Project(BaseModel, allow_population_by_field_name=True):
    """
    Project.

    :param name (str): Unique name.
    :param remote (str): Remote Alias
    :param sub_url (str): URL relative to remote urlbase.
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
    manifest: Optional["Manifest"] = None

    @root_validator
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

    :param defaults (Defaults): Default settings
    :param remotes (List[Remote]): Remote Aliases
    """

    filepath: Optional[Path] = None
    defaults: Defaults = Defaults()
    remotes: List[Remote] = []
    projects: List[Project] = []

    def resolve(self, manifest_url=None) -> "Manifest":
        """
        Return Manifest with `defaults` and `remotes` populated.

        :param manifest_url: Manifest URL

        `defaults` and `remotes` are untouched.
        The project `name` and `manifest` is untouched.
        The `url` is calculated if not given based on the remote and `name`.
        The `remote` is cleared.
        The `path` defaults to `name` if not given.
        """
        return Manifest(
            filepath=self.filepath,
            defaults=self.defaults,
            remotes=self.remotes,
            projects=[self._resolve_project(project, manifest_url) for project in self.projects],
        )

    def _resolve_project(self, project, manifest_url):
        url = project.url
        if not url:
            # URL assembly
            project_remote = project.remote or self.defaults.remote
            project_sub_url = project.sub_url or project.name
            for remote in self.remotes:
                if remote.name == project_remote:
                    url = f"{remote.urlbase}/{project_sub_url}"
                    break
            else:
                raise ValueError(f"Unknown remote {project.remote} for project {project.name}")
        # Resolve relative URLs
        url = urljoin(manifest_url, url)
        return Project(
            name=project.name,
            remote=None,
            url=url,
            revision=project.revision or self.defaults.revision,
            path=project.path or project.name,
            manifest=project.manifest,
        )


Project.update_forward_refs()


def create_project_filter(project_paths: Optional[List[Path]] = None) -> Callable[[Project], bool]:
    """Create filter function."""
    if project_paths:
        initialized_project_paths: List[Path] = project_paths
        return lambda project: project.path in initialized_project_paths
    return lambda _: True
