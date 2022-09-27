"""Refined :any:`pydantic.BaseModel`."""
import pydantic


class BaseModel(pydantic.BaseModel):
    """Refined :any:`pydantic.BaseModel`."""

    def __repr_args__(self: pydantic.BaseModel):
        return [
            (key, value) for key, value in self.__dict__.items() if value is not self.__fields__[key].field_info.default
        ]
