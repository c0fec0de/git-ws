"""
Multi Repository Management Tool.

`AnyRepo` is a simple and lean multi repository management tool, with the following features:

* Git-like command line interface
* Dependency and transient dependency handling
* Relative URL support

The :any:`AnyRepo` class provides a simple programmatic interface similar to the command line interface.
See :any:`AnyRepo` for any details.
"""

import logging

from .anyrepo import AnyRepo
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
)
from .filters import Filter
from .git import Git
from .iters import ManifestIter, ProjectIter
from .workspace import Workspace
from .workspacefinder import find_workspace
