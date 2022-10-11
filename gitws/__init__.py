"""
Git Workspace - Multi Repository Management Tool.

`git ws` is a simple and lean multi repository management tool, with the following features:

* Integrated into git command line interface
* Dependency and transient dependency handling
* Relative URL support

The :any:`GitWS` class provides a simple programmatic interface similar to the command line interface.
See :any:`GitWS` for any details.
"""

import logging

from .appconfig import AppConfig, AppConfigLocation
from .clone import Clone, map_paths
from .datamodel import AppConfigData, Defaults, Group, Manifest, ManifestSpec, Project, ProjectSpec, Remote
from .exceptions import (
    GitCloneMissingError,
    GitCloneNotCleanError,
    InitializedError,
    InvalidConfigurationFileError,
    InvalidConfigurationLocationError,
    ManifestError,
    ManifestExistError,
    ManifestNotFoundError,
    NoGitError,
    OutsideWorkspaceError,
    UninitializedError,
    WorkspaceNotEmptyError,
)
from .filters import Filter
from .git import Git
from .gitws import GitWS
from .iters import ManifestIter, ProjectIter
from .workspace import Workspace
from .workspacefinder import find_workspace
