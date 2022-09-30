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
from .exceptions import (
    GitCloneMissingError,
    InitializedError,
    ManifestExistError,
    ManifestNotFoundError,
    NoGitError,
    OutsideWorkspaceError,
    UninitializedError,
)
