# Copyright 2022-2023 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Refined :any:`pydantic.BaseModel`."""
from typing import Any, Dict

import pydantic

from ._stringconverter import StringConverter


class BaseModel(pydantic.BaseModel):
    """
    Refined :any:`pydantic.BaseModel`.

    * Data Models are immutable.
    * The ``repr`` implementation skips fields, which are identical to their default value.
    * A ``new`` implementation eases the creation of new instances with the same values.
    """

    model_config = pydantic.ConfigDict(frozen=True)

    def __repr_args__(self: pydantic.BaseModel):
        fields = self.model_fields
        return [
            (key, value) for key, value in self.__dict__.items() if key not in fields or value != fields[key].default
        ]

    def model_copy(self, *, update=None, **kwargs):
        obj = super().model_copy(update=update, **kwargs)
        obj.model_validate(obj)
        return obj

    def model_copy_fromstr(self, kwargs: Dict[str, Any]):
        """Create new instance with updated arguments."""
        converter = StringConverter(properties=self.model_json_schema(by_alias=False)["properties"])
        update = {}
        for name, value in kwargs.items():
            update[name] = converter(name, value)
        return self.model_copy(update=update)
