"""Types."""
from typing import Callable, Optional

from .manifest import Project

Groups = Optional[str]
ProjectFilter = Callable[[Project], bool]
