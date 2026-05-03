"""
Module containing useful generator functions that represent musical processes.
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

import random


def random_walk(start_value, step=1, turn_around_chance=0.5, clamp_min=None, clamp_max=None):
    """
    Returns a generator starting on `start_value` that randomly walks between `clamp_min` and `clamp_max`, using a
    step size of `step`, and turning around with probability `turn_around_chance`

    :param start_value: walk start value
    :param step: walk step size
    :param turn_around_chance: probability of turning around (affects wiggliness)
    :param clamp_min: random walk bounces off of this lower limit. If None, walk can go arbitrarily low.
    :param clamp_max: random walk bounces off of this upper limit. If None, walk can go arbitrarily high.
    """
    x = start_value
    current_step = random.choice([-step, step])
    while True:
        x += current_step
        if clamp_min is not None and x < clamp_min:
            current_step = step
            x += 2 * step
        elif clamp_max is not None and x > clamp_max:
            current_step = -step
            x -= 2 * step
        else:
            if random.random() < turn_around_chance:
                current_step *= -1
        yield x


def non_repeating_shuffle(input_list, stop_after=float("inf"), insertion_threshold=0.5):
    """
    Returns a generator that randomly selects items from the input list, avoiding repeat selections.

    :param input_list: the list to shuffle through
    :param stop_after: stops after returning this many items
    :param insertion_threshold: how close to insert an item back in the deck after it has been selected. When close to
        1, the same item can be returned in close proximity to itself, when close to 0, we cycle through almost every
        other item before getting the same item again. (At 0, becomes a deterministic repeated shuffle.)
    """
    deck = list(input_list)
    max_insert_point = int(len(input_list) * insertion_threshold)
    random.shuffle(deck)
    while stop_after > 0:
        top_card = deck.pop()
        yield top_card
        deck.insert(random.randint(0, max_insert_point), top_card)
        stop_after -= 1
