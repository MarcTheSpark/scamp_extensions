"""
Module containing generators for the fibonacci sequence and its relatives, including the cycles that arise
from taking such a sequence modulo some number (the Pisano periods).
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


import itertools


def fibonacci(seed_values=(0, 1)):
    """
    A simple fibonacci generator function

    :param seed_values: by default (0, 1), but other seeds lead to other sequences (e.g. (2, 1) -> lucas numbers)
    """
    a, b = seed_values
    yield a
    while True:
        a, b = b, a + b
        yield a


def fibonacci_cycle(modulo, seed=(0, 1), num_cycles=None, num_values=None, return_pairs=False):
    """
    Gets the cycle of fibonacci (or related) numbers with the given modulo and pair of seed values. If num_cycles is
    set, we do a given number of full cycles; if num values is set, we do a given number of values, and if neither is
    set, this continues infinitely.

    :param modulo: the modulo we use
    :param seed: the first two numbers to start with
    :param num_cycles: how many cycles to return
    :param num_values: how many values to return
    :param return_pairs: returns pairs of adjacent values (e.g. [(0, 1), (1, 1), (1, 2), (2, 3), (3, 5)...], since these
        pairs of numbers represent the state space of the fibonacci cycles
    """
    a, b = seed[0] % modulo, seed[1] % modulo

    if num_values is not None and num_cycles is not None:
        raise ValueError("Only one of `num_values` or `num_cycles` may be set")
    while num_values > 0 if num_values is not None \
            else num_cycles > 0 if num_cycles is not None \
            else True:
        yield (a, b) if return_pairs else a
        a, b = b, (a + b) % modulo
        if num_cycles is not None and (a, b) == seed:
            num_cycles -= 1
        elif num_values is not None:
            num_values -= 1


def _first_key(ordered_dict):
    for key in ordered_dict:
        return key


def all_fibonacci_cycles(modulo, return_pairs=False):
    """
    For a given modulo, get a list of all possible cycles using the fibonacci recurrence relation.

    :param modulo: the modulo to subject the fibonacci sequences to
    :param return_pairs: if true, return pairs of adjacent values (since this is the state space)
    """
    points_remaining = dict.fromkeys(itertools.product(range(modulo), range(modulo)), None)
    cycles = []
    while len(points_remaining) > 0:
        start_point = _first_key(points_remaining)
        this_cycle = []
        for point in fibonacci_cycle(modulo, start_point, 1, return_pairs=True):
            this_cycle.append(point if return_pairs else point[0])
            del points_remaining[point]
        cycles.append(this_cycle)
    return cycles

