"""
Module containing the :class:`MarkovModel` and :class:`MarkovIterator` classes for analyzing and resynthesizing a
sequence based on Markov analysis. Capable of fractional order resynthesis.
Relies upon an embedded copy of the `pykov` (https://github.com/riccardoscalco/Pykov) library, which in turn relies
upon the `numpy`, `scipy`, and `six` libraries.
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

from __future__ import annotations
import random
import math
from typing import Sequence
from ..utilities.sequences import cyclic_slice


class MarkovModel:

    """
    A Markov analysis-synthesis tool that analyzes the given data, and can generate new data based on the
    same statistical patterns.

    :param data: A sequence of states whose transition probabilities to analyze (can train after instantiating too)
    :param max_order: The maximum order of Markov analysis to perform
    :param cyclic: Whether or not to treat the data as cyclic. (If not, resynthesis can reach a dead end.)
    """

    def __init__(self, data: Sequence = None, max_order: int = 1, cyclic: bool = True):
        self.state_quantities = {}
        self.num_states = 0

        self.max_order = max_order

        # we import this inside of MarkovModel so that a lack of dependencies does not break unrelated imports
        # in the scamp_extensions.process subpackage.
        from ._pykov import Chain
        self.chain = Chain()
        
        if data:
            self.train(data, cyclic)

    def move_zeroth_order(self):
        """
        Returns a randomly selected state (weighted by frequency).
        """
        r = random.random()
        for key, value in self.state_quantities.items():
            this_key_probability = value/self.num_states
            if r < this_key_probability:
                return key
            else:
                r -= this_key_probability

    def generate(self, num_values: int, order: float, initial_history: Sequence = None,
                 keep_looping: bool = False) -> Sequence:
        """
        Generates a sequence of states following the Markov analysis performed on the input data.

        :param num_values: How many states to generate.
        :param order: The Markov order used in generating new states. Can be floating point, in which case the order for
            any given move is a weighted random choice between the adjacent integer orders.
        :param initial_history: Values with which to seed the state history. If none, simply starts at random state
            from within the data set.
        :param keep_looping: if True, then when we hit a dead end, keep reducing the order by one until we find a next
            move (once it gets to order zero, it just chooses randomly)
        """
        if order > self.max_order:
            raise ValueError("Cannot generate values using order {}, as max order was set to {}.".
                             format(order, self.max_order))

        if initial_history is None:
            initial_history = (self.move_zeroth_order(),)
        elif not hasattr(initial_history, '__len__'):
            initial_history = (initial_history,)

        history = list(initial_history)
        out = []

        try:
            while len(out) < num_values:
                if keep_looping:
                    o = order
                    while True:
                        try:
                            next_move = self._get_next(history, o)
                            break
                        except KeyError:
                            # no data for this order; try reducing order
                            o -= 1
                else:
                    next_move = self._get_next(history, order)
                out.append(next_move)
                history.append(next_move)
        finally:
            return out

    def _get_next(self, history, order: float):
        if order <= 0:
            return self.move_zeroth_order()

        if order != int(order):
            # fractional order, so choose the higher or lower order with appropriate probability
            lower_order = int(order)
            higher_order = lower_order + 1
            fractional_part = order - lower_order
            order = higher_order if random.random() < fractional_part else lower_order

        if len(history) > order:
            this_key = tuple(history[len(history) - int(order):])
        else:
            this_key = tuple(history)
        return self.move(this_key)

    def move(self, state, random_func=None):
        """
        Do one step from the indicated state, and return the final state.
        Optionally, a function that generates a random number can be supplied.
        """
        return self.chain.move(state, random_func)

    def _count_states(self, data):
        # for generating zeroth-order
        for datum in data:
            if datum in self.state_quantities:
                self.state_quantities[datum] += 1.0
            else:
                self.state_quantities[datum] = 1.0
            self.num_states += 1

    def train(self, data, cyclic=True):
        self._count_states(data)

        order = int(math.ceil(self.max_order)) if not isinstance(self.max_order, int) else self.max_order

        if order >= len(data):
            order = len(data)

        for o in range(1, order+1):
            if cyclic:
                start_indices = range(len(data))
            else:
                start_indices = range(len(data) - o)

            for i in start_indices:
                this_key = (tuple(cyclic_slice(data, i, i+o)), data[(i+o) % len(data)])
                if this_key in self.chain.keys():
                    self.chain[this_key] += 1
                else:
                    self.chain[this_key] = 1

        self._normalize_probabilities()

    def _normalize_probabilities(self):
        antecedent_total_prob_values = {}
        for (antecedent, consequent) in self.chain:
            if antecedent in antecedent_total_prob_values:
                antecedent_total_prob_values[antecedent] += self.chain[(antecedent, consequent)]
            else:
                antecedent_total_prob_values[antecedent] = float(self.chain[(antecedent, consequent)])

        for (antecedent, consequent) in self.chain:
            self.chain[(antecedent, consequent)] = \
                self.chain[(antecedent, consequent)] / antecedent_total_prob_values[antecedent]

    def get_iterator(self, order: float, start_values: Sequence = None, keep_looping: bool = False) -> MarkovIterator:
        """
        Returns a :class:`MarkovIterator` based on this model.

        :param order: the Markov order to use in generating new states. Can be floating point (see
            :class:`MarkovIterator`), and can be altered during iteration.
        :param start_values: Values with which to seed the iterator's history. If none, simply starts at random state
            from within the data set.
        :param keep_looping: if True, then when we hit a dead end, keep reducing the order by one until we find a next
            move (once it gets to order zero, it just chooses randomly)
        """
        return MarkovIterator(self, order, start_values, keep_looping)


class MarkovIterator:

    """
    Iterator that returns generated values from the given MarkovModel. Order can be fractional and can change
    during iteration.

    :param markov_model: the MarkovModel used for resynthesis.
    :param order: the Markov order used in generating new states. Can be floating point, in which case the order for
        any given move is a weighted random choice between the adjacent integer orders.
    :param start_values: Values with which to seed this iterator's history. If none, simply starts at random state
        from within the data set.
    :param keep_looping: if True, then when we hit a dead end, keep reducing the order by one until we find a next
            move (once it gets to order zero, it just chooses randomly)
    """

    def __init__(self, markov_model: MarkovModel, order: float, start_values: Sequence = None,
                 keep_looping: bool = False):
        if start_values is None:
            self.history = [markov_model.move_zeroth_order()]
        else:
            self.history = list(start_values)

        self.model = markov_model
        self.order = order
        self.keep_looping = keep_looping

    def __iter__(self):
        return self

    def __next__(self):
        self.history.extend(self.model.generate(1, self.order, self.history, self.keep_looping))
        if len(self.history) > self.model.max_order:
            self.history.pop(0)
        return self.history[-1]
