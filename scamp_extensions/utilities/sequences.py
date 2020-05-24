"""
Subpackage containing utility functions for manipulating lists/sequences (some of which are imported from
:mod:`scamp.utilities`).
"""

from itertools import count, chain
from typing import Sequence
from scamp.utilities import make_flat_list, sum_nested_list


def rotate_sequence(s: Sequence, n: int) -> Sequence:
    """
    Rotates a sequence s such that it begins with element l[n] and wraps back around to l[n-1].

    :param s: the list to rotate
    :param n: number of elements to shift by (can be negative and/or greater than the length of l)
    :return: a "rotated" version of the input sequence
    """
    return s[n:] + s[:n]


def sequence_depth(seq: Sequence):
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
