"""Filters."""
from typing import Optional, Tuple

from ._basemodel import BaseModel


class Filter(BaseModel):

    """
    Filter.

    Keyword Args:
        only: Limit to these only. Highest precedence.
        without: Deselected.
        with_: Selected optionals. Lowest precedence.

    A simple example:

    >>> filter_ = Filter.from_spec("+doc,-test")
    >>> filter_
    Filter(with_=('doc',), without=('test',))
    >>> filter_(('other', ))
    True
    >>> filter_(('doc', ))
    True
    >>> filter_(('test', ))
    False

    The following table describes the full behaviour:

    >>> from tabulate import tabulate
    >>> specs = ("", "test", "+test", "-test", "+doc,-test", "-doc,+test")
    >>> values = (tuple(), ('test',), ('test', 'doc'), ('lint', 'doc'))
    >>> filters = [Filter.from_spec(spec) for spec in specs]
    >>> disabled = None
    >>> overview = [[value] + [filter_(value, disabled=disabled) for filter_ in filters] for value in values]
    >>> print(tabulate(overview, headers = ["value / spec",] + [f"{spec!r}" for spec in specs]))
    value / spec     ''    'test'    '+test'    '-test'    '+doc,-test'    '-doc,+test'
    ---------------  ----  --------  ---------  ---------  --------------  --------------
    ()               True  False     True       True       True            True
    ('test',)        True  True      True       False      False           True
    ('test', 'doc')  True  True      True       False      False           False
    ('lint', 'doc')  True  False     True       True       True            False

    The `disabled` option defines the default behaviour, which is overwritten by `with`:

    >>> filter_ = Filter()
    >>> filter_(('test', ), disabled=('test',))
    False
    >>> filter_ = Filter(with_=('test',))
    >>> filter_(('test', ), disabled=('test',))
    True

    The following table describes the full behaviour with `disabled=('test', )`:

    >>> disabled = ('test', )
    >>> overview = [[value] + [filter_(value, disabled=disabled) for filter_ in filters] for value in values]
    >>> print(tabulate(overview, headers = ["value / spec",] + [f"{spec!r}" for spec in specs]))
    value / spec     ''     'test'    '+test'    '-test'    '+doc,-test'    '-doc,+test'
    ---------------  -----  --------  ---------  ---------  --------------  --------------
    ()               True   False     True       True       True            True
    ('test',)        False  True      True       False      False           True
    ('test', 'doc')  False  True      True       False      False           False
    ('lint', 'doc')  True   False     True       True       True            False
    """

    only: Tuple[str, ...] = tuple()
    with_: Tuple[str, ...] = tuple()
    without: Tuple[str, ...] = tuple()

    @staticmethod
    def from_spec(expr: str) -> "Filter":
        """
        Create :any:`Filter` from `expr`.

        >>> Filter.from_spec("")
        Filter()
        >>> Filter.from_spec("+test")
        Filter(with_=('test',))
        >>> Filter.from_spec("-test,-doc, +lint, imp")
        Filter(only=('imp',), with_=('lint',), without=('test', 'doc'))
        >>> Filter.from_spec("+lint, -doc")
        Filter(with_=('lint',), without=('doc',))
        """
        parts = tuple(part.strip() for part in expr.split(",") if part.strip())
        only = tuple(part for part in parts if not part.startswith(("+", "-")))
        with_ = tuple(part[1:] for part in parts if part.startswith("+"))
        without = tuple(part[1:] for part in parts if part.startswith("-"))
        return Filter(only=only, with_=with_, without=without)

    def __call__(self, items: Tuple[str, ...], disabled: Optional[Tuple[str, ...]] = None) -> bool:
        itemsset = set(items)

        # ONLY
        onlyset = set(self.only)
        if onlyset:
            return bool(onlyset & itemsset)

        # Trivia
        if not itemsset:
            return True

        # WITHOUT
        withoutset = set(self.without)
        if itemsset & withoutset:
            return False

        # WITH
        disableditems = set(disabled or tuple()) & itemsset
        withset = set(self.with_)
        if disableditems & withset:
            return True

        # DISABLE
        return not bool(disableditems)
