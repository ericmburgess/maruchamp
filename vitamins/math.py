"""math.py -- mathy vitamins"""
from bisect import bisect_right
from math import *


def clamp(val, lo=-1, hi=1):
    return max(lo, min(val, hi))


def is_close(val1, val2, tol=1e-6):
    return abs(val2 - val1) < tol


def is_between(lo, val, hi) -> bool:
    return (lo <= val <= hi) or (lo >= val >= hi)


def is_between_strict(lo, val, hi) -> bool:
    return (lo < val < hi) or (lo > val > hi)


class Lerp:
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
