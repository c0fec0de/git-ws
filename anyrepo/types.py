"""Types."""
from typing import Callable, Optional

from .datamodel import Project

Groups = Optional[str]
ProjectFilter = Callable[[Project], bool]
