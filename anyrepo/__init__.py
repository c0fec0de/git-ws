"""Multi Repository Management Tool."""

import logging

from .anyrepo import AnyRepo
from .exceptions import NoGitError, UninitializedError

logging.getLogger(__name__)
