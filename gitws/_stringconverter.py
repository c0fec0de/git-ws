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

"""String Converter."""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class StringConverter(BaseModel):
    """
    String Converter.

    >>> properties = {'name': {'type': 'boolean'}, 'empty': {'type': 'null'}, 'bar': {'type': 'unknown'}}
    >>> converter = StringConverter(properties=properties)
    >>> converter('name', 'yes')
    True
    >>> converter('name', 'NO')
    False
    >>> converter('empty', '')
    >>> converter('empty', 'value')
    Traceback (most recent call last):
      ...
    ValueError: 'empty': 'value'
    >>> converter('name', '')
    Traceback (most recent call last):
      ...
    ValueError: 'name': ''
    >>> converter('bar', '')
    Traceback (most recent call last):
      ...
    ValueError: 'bar': ''
    """

    properties: Dict[str, Any]

    def __call__(self, name, value: Optional[str]) -> Any:
        value = (value or "").strip()
        properties = self.properties[name]
        if "type" in properties:
            specs = [properties]
        elif "anyOf" in properties:
            specs = properties["anyOf"]
        else:
            raise RuntimeError(f"Unknown properties {properties}")
        return self._convert(specs, name, value)

    @staticmethod
    def _convert(specs, name, value):  # noqa: C901
        for spec in specs:
            type_ = spec["type"]
            if type_ == "null":
                if not value:
                    return None
            elif type_ == "string":
                if isinstance(value, str) and value:
                    return value
            elif type_ == "boolean":
                if value.lower() in ("yes", "y", "true", "1"):
                    return True
                if value.lower() in ("no", "n", "false", "1"):
                    return False
            elif type_ == "array":
                assert spec["items"] == {"type": "string"}
                if value:
                    items = [item.strip() for item in value.split(",")]
                    return tuple(item for item in items if item)
                return ()
        raise ValueError(f"{name!r}: {value!r}")
