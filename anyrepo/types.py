"""General Types."""
from typing import Callable, Optional

from .datamodel import Project

Groups = Optional[str]
"""Groups Specification."""

ProjectFilter = Callable[[Project], bool]
"""Project Filter Function."""
