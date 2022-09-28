"""Refined :any:`pydantic.BaseModel`."""
import pydantic


class BaseModel(pydantic.BaseModel):
    """Refined :any:`pydantic.BaseModel`."""

    class Config:
        """Configure."""

        # pylint: disable=too-few-public-methods
        allow_mutation = False

    def __repr_args__(self: pydantic.BaseModel):
        return [
            (key, value) for key, value in self.__dict__.items() if value is not self.__fields__[key].field_info.default
        ]

    def new(self, **kwargs):
        """Create new instance with updated arguments."""
        data = self.dict()
        data.update(kwargs)
        return self.__class__(**data)
