"""
Subpackage containing utility functions for manipulating lists/sequences (some of which are imported from
:mod:`scamp.utilities`).
"""

#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  #
#  This file is part of SCAMP (Suite for Computer-Assisted Music in Python)                      #
#  Copyright © 2020 Marc Evanstein <marc@marcevanstein.com>.                                     #
#                                                                                                #
#  This program is free software: you can redistribute it and/or modify it under the terms of    #
#  the GNU General Public License as published by the Free Software Foundation, either version   #
#  3 of the License, or (at your option) any later version.                                      #
#                                                                                                #
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;     #
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.     #
#  See the GNU General Public License for more details.                                          #
#                                                                                                #
#  You should have received a copy of the GNU General Public License along with this program.    #
#  If not, see <http://www.gnu.org/licenses/>.                                                   #
#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  #

from itertools import count, chain
from typing import Sequence
from scamp.utilities import make_flat_list, sum_nested_list
from functools import wraps
import re


def rotate_sequence(s: Sequence, n: int) -> Sequence:
    """
    Rotates a sequence s such that it begins with element l[n] and wraps back around to l[n-1].

    :param s: the list to rotate
    :param n: number of elements to shift by (can be negative and/or greater than the length of l)
    :return: a "rotated" version of the input sequence
    """
    return s[n:] + s[:n]


def cyclic_slice(l: Sequence, start: int, end: int) -> Sequence:
    """
    Takes a slice that loops back to the beginning if end is before start

    :param l: the list to slice
    :param start: start index
    :param end: end index
    :return: list representing the cyclic slice
    """

    if end >= start:
        # start by making both indices positive, since that's easier to handle
        while start < 0 or end < 0:
            start += len(l)
            end += len(l)
        if end >= start + len(l):
            out = []
            while end - start >= len(l):
                out.extend(l[start:] + l[:start])
                end -= len(l)
            out += cyclic_slice(l, start, end)
            return out
        else:
            end = end % len(l)
            start = start % len(l)
            if end >= start:
                return l[start:end]
            else:
                return l[start:] + l[:end]
    else:
        # if the end is before the beginning, we do a backwards slice
        # basically this means we reverse the list, and recalculate the start and end
        new_start = len(l) - start - 1
        new_end = len(l) - end - 1
        new_list = list(l)
        new_list.reverse()
    return cyclic_slice(new_list, new_start, new_end)


def sequence_depth(seq: Sequence) -> int:
    """
    Find the maximum _depth of any element in a nested sequence. Slightly adapted from pillmuncher's answer here:
    https://stackoverflow.com/questions/6039103/counting-depth-or-the-deepest-level-a-nested-list-goes-to

    :param seq: a nested Sequence (list, tuple, etc)
    :return: int representing maximum _depth
    """
    if not isinstance(seq, Sequence):
        return 0
    seq = iter(seq)
    try:
        for level in count():
            seq = chain([next(seq)], seq)
            seq = chain.from_iterable(s for s in seq if isinstance(s, Sequence))
    except StopIteration:
        return level


# ------------------------------------ Sequence-optional function decorators -----------------------------------------


def multi_option_function(f):
    """
    Decorator that allows the first argument of the function to be a list, tuple, or iterator, and in that case
    performs the function one each element individually, returning a list, tuple, or iterator.

    :param f: the function, taking at least one argument
    :return: a wrapped version that can take list, tuple, or iterator
    """
    # adds an extra note to the docstring saying it supports lists/etc.
    insert_index = _get_docstring_insert_position(f.__doc__)
    f.__doc__ = f.__doc__[:insert_index] + \
                "\n    The first argument can optionally be a list, tuple, or iterator," \
                " in which case this is performed on each element." + \
                f.__doc__[insert_index:]

    @wraps(f)
    def wrapper(*args, **kwds):
        if isinstance(args[0], list):
            return [f(x, *args[1:], **kwds) for x in args[0]]
        elif isinstance(args[0], tuple):
            return tuple(f(x, *args[1:], **kwds) for x in args[0])
        elif hasattr(args[0], '__next__'):
            return (f(x, *args[1:], **kwds) for x in args[0])
        return f(*args, **kwds)
    return wrapper


def multi_option_method(f):
    """
    Same as :func:`multi_option_function`, but used to decorate methods instead of functions.

    :param f: the method, taking at least one argument
    :return: a wrapped version that can take list, tuple, or iterator
    """
    # adds an extra note to the docstring saying it supports lists/etc.
    insert_index = _get_docstring_insert_position(f.__doc__)
    f.__doc__ = f.__doc__[:insert_index] + \
                "\n        The first argument can optionally be a list, tuple, or iterator," \
                " in which case this is performed on each element." + \
                f.__doc__[insert_index:]

    @wraps(f)
    def wrapper(*args, **kwds):
        if isinstance(args[1], list):
            return [f(args[0], x, *args[2:], **kwds) for x in args[1]]
        elif isinstance(args[1], tuple):
            return tuple(f(args[0], x, *args[2:], **kwds) for x in args[1])
        elif hasattr(args[1], '__next__'):
            return (f(args[0], x, *args[2:], **kwds) for x in args[1])
        return f(*args, **kwds)
    return wrapper


def _get_docstring_insert_position(docstring):
    # first insert before ":param" and any spaces before that
    end_of_description = re.search(r'[\s\n]*:param', docstring)
    # if ":param" doesn't show up, insert before any spaces or returns at the end of the docstring
    if end_of_description is None:
        end_of_description = re.search(r'[\s\n]*$', docstring)
    # as a last resort, just stick it at the end
    insert_index = end_of_description.start() if end_of_description is not None else -1
    return insert_index
