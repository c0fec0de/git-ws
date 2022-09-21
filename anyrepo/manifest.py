"""
Manifest Data Container.

The :any:`Manifest` and :any:`Project` classes are pure data container.
They do not implement any business logic.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, root_validator

from ._url import urljoin


class Remote(BaseModel):
    """
    Remote Alias

    Args:
        name: Remote Name
    Keyword Args:
        urlbase: Base URL. Optional.
    """

    name: str
    urlbase: Optional[str] = None


class Defaults(BaseModel):
    """
    Default Values

    Keyword Args:
        remote: Remote Name
        revision: Revision
    """

    remote: Optional[str] = None
    revision: Optional[str] = None


class Project(BaseModel):
    """
    Project.

    Args:
        name (str): Unique name.

    Keyword Args:
        remote (str): Remote Alias
        suburl (str): URL relative to remote urlbase.
        url (str): URL
        revision (str): Revision
        path (str): Project Filesystem Path. Relative to Workspace Directory.
    """

    name: str
    remote: Optional[str] = None
    suburl: Optional[str] = None
    url: Optional[str] = None
    revision: Optional[str] = None
    path: Optional[str] = None
    manifest: "Manifest" = None

    @root_validator
    def _remote_or_url(cls, values):
        # pylint: disable=no-self-argument,no-self-use
        remote = values.get("remote", None)
        suburl = values.get("suburl", None)
        url = values.get("url", None)
        if remote and url:
            raise ValueError("'remote' and 'url' are mutally exclusive")
        if url and suburl:
            raise ValueError("'url' and 'suburl' are mutally exclusive")
        if suburl and not remote:
            raise ValueError("'suburl' requires 'remote'")
        return values


class Manifest(BaseModel):

    """
    Manifest.

    Keyword Args:
        defaults (Defaults): Default settings
        remotes (List[Remote]): Remote Aliases
    """

    filepath: Optional[Path] = None
    defaults: Defaults = Defaults()
    remotes: List[Remote] = []
    projects: List[Project] = []

    def resolve(self, manifesturl=None) -> "Manifest":
        """
        Return Manifest with `defaults` and `remotes` populated.

        Keyword Args:
            manifesturl: Manifest URL

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
            projects=[self._resolve_project(project, manifesturl) for project in self.projects],
        )

    def _resolve_project(self, project, manifesturl):
        url = project.url
        if not url:
            # URL assembly
            projectremote = project.remote or self.defaults.remote
            projectsuburl = project.suburl or project.name
            for remote in self.remotes:
                if remote.name == projectremote:
                    url = f"{remote.urlbase}/{projectsuburl}"
                    break
            else:
                raise ValueError(f"Unknown remote {project.remote} for project {project.name}")
        # Resolve relative URLs
        url = urljoin(manifesturl, url)
        return Project(
            name=project.name,
            remote=None,
            url=url,
            revision=project.revision or self.defaults.revision,
            path=project.path or project.name,
            manifest=project.manifest,
        )


Project.update_forward_refs()


def create_project_filter(project_paths: Optional[List[Path]] = None):
    """Create filter function."""
    if project_paths:
        return lambda project: project.path in project_paths
    return lambda _: True
