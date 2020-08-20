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
