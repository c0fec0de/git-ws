# Copyright 2022 c0fec0de
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
import pydantic


class BaseModel(pydantic.BaseModel, allow_mutation=False):
    """
    Refined :any:`pydantic.BaseModel`.

    * Data Models are immutable.
    * The `repr` implementation skips fields, which are identical to their default value.
    * A `new` implementation eases the creation of new instances with the same values.
    """

    def __repr_args__(self: pydantic.BaseModel):
        return [
            (key, value) for key, value in self.__dict__.items() if value != self.__fields__[key].field_info.default
        ]

    def update(self, **kwargs):
        """Create new instance with updated arguments."""
        return self.__update(kwargs)

    def update_fromstr(self, kwargs):
        """Create new instance with updated arguments."""
        fields = self.schema()["properties"]
        data = {}
        for name, value in kwargs.items():
            data[name] = self.__fromstr(fields[name]["type"], value)
        return self.__update(data)

    def __update(self, kwargs):
        data = self.dict()
        data.update(kwargs)
        return self.__class__(**data)

    @staticmethod
    def __fromstr(type_, value):
        if type_ == "string":
            return value
        if type_ == "array":
            if value:
                return tuple(item.strip() for item in value.split(","))
            return tuple()
        if type_ == "boolean":
            if value:
                return value.lower() in ("true", "1", "on")
            return None
        assert False, f"Unknown type {type_}"  # pragma: no cover
