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
        data = self.dict()
        data.update(kwargs)
        return self.__class__(**data)
