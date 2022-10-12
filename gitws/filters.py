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

"""Filters."""
from typing import Any, Optional, Tuple

from ._basemodel import BaseModel


def default_filter(item: Any) -> bool:
    """Default Filter - always returning True."""
    # pylint: disable=unused-argument
    return True


class Filter(BaseModel):

    """
    A Generic Filter With A String Interface.

    Keyword Args:
        only: Limit to these only. Highest precedence.
        without: Deselected.
        with_: Selected optionals. Lowest precedence.

    A simple example:

    >>> filter_ = Filter.from_str("+doc,-test")
    >>> filter_
    Filter(without=('test',), with_=('doc',))
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
    >>> filters = [Filter.from_str(spec) for spec in specs]
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
    """Only select items matching. Highest Precedence."""

    without: Tuple[str, ...] = tuple()
    """Deselect items matching. Mid Precedence."""

    with_: Tuple[str, ...] = tuple()
    """Include optional items matching. Lowest Precedence."""

    @staticmethod
    def from_str(expr: str) -> "Filter":
        """
        Create :any:`Filter` from `expr`.

        >>> Filter.from_str("")
        Filter()
        >>> Filter.from_str("+test")
        Filter(with_=('test',))
        >>> Filter.from_str("-test,-doc, +lint, imp")
        Filter(only=('imp',), without=('test', 'doc'), with_=('lint',))
        >>> Filter.from_str("+lint, -doc")
        Filter(without=('doc',), with_=('lint',))
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
