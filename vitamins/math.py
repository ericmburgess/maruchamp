"""The `vitamins.math` module contains a few helper routines that may sometimes be
useful for bot developers. It also includes all of Python's standard `math` library, so
the following will give you access to all the routines documented here, as well as
all of Python's `math` module:


.. sourcecode:: python

    from vitamins.math import *

"""
from bisect import bisect_right
from math import *


def clamp(val, lo=-1, hi=1):
    """Shorthand for `max(lo, min(val, hi))`. """
    return max(lo, min(val, hi))


def is_close(val1, val2, tol=1e-6):
    """Shorthand for `abs(val2 - val1) < tol`."""
    return abs(val2 - val1) < tol


def is_between(lo, val, hi) -> bool:
    """Shorthand for `(lo <= val <= hi) or (lo >= val >= hi)`."""
    return (lo <= val <= hi) or (lo >= val >= hi)


def is_between_strict(lo, val, hi) -> bool:
    """Shorthand for `(lo < val < hi) or (lo > val > hi)`."""
    return (lo < val < hi) or (lo > val > hi)


class Lerp:
    """One-dimensional linear interpolator.

    :param x_list: The x-values to be interpolated between. Must be in strictly
        ascending order.
    :param y_list: The corresponding y-values. Must have the same length as `x_values`.
    :param clamp: If True, input values outside the range of `x_list` will be
        forced to the lowest or highest value. If False, then `ValueError` will be
        raised instead.

    .. sourcecode:: python

        >>> from vitamins.math import Lerp
        >>> lerp = Lerp([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 4.0, 9.0], clamp=True)
        >>> lerp(0)
        0.0
        >>> lerp(0.5)
        0.5
        >>> lerp(2.5)
        6.5
        >>> lerp(100)
        9.0
    """

    def __init__(self, x_list, y_list, clamp=False):
        if any(y - x <= 0 for x, y in zip(x_list, x_list[1:])):
            raise ValueError("x_list must be in strictly ascending order!")
        self.x_list = x_list
        self.y_list = y_list
        intervals = zip(x_list, x_list[1:], y_list, y_list[1:])
        self.slopes = [(y2 - y1) / (x2 - x1) for x1, x2, y1, y2 in intervals]
        self.clamp = clamp

    def __call__(self, x):
        if not (self.x_list[0] <= x <= self.x_list[-1]):
            if self.clamp:
                x = clamp(x, self.x_list[0], self.x_list[-1])
            else:
                raise ValueError(f"x={x} out of bounds!")
        if x == self.x_list[-1]:
            return self.y_list[-1]
        i = bisect_right(self.x_list, x) - 1
        return self.y_list[i] + self.slopes[i] * (x - self.x_list[i])
