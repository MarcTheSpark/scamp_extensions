"""
Module containing the :class:`LSystem` class, a simple implementation of a Lindenmayer system.
(See https://en.wikipedia.org/wiki/L-system).
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

from typing import MutableMapping, Any, Tuple
from functools import lru_cache
import random


class LSystem:
    """
    Simple implementation of an LSystem. Each generation is a string consisting of an alphabet of characters.
    Optionally, these characters can be assigned meanings.

    :param seed_string: the initial string
    :param production_rules: dictionary describing how each letter evolves in a subsequent generation. Any letter
        not found in the dictionary is assumed to be a constant. Also, stochastic rules are possible by providing
        a list or tuple of outcomes for a given letter, or a list/tuple consisting of a list of outcomes and a
        list of weightings.
    :param meanings: (optional) dictionary specifying the meaning of each letter. Should contain an entry for every
        letter potentially encountered.
    :ivar seed: the initial string
    :ivar rules: dictionary describing how each letter evolves in a subsequent generation. Any letter
        not found in the dictionary is assumed to be a constant
    :ivar meanings: (optional) dictionary specifying the meaning of each letter. Should contain an entry for every
        letter potentially encountered.
    """

    def __init__(self, seed_string: str, production_rules: MutableMapping[str, str],
                 meanings: MutableMapping[str, Any] = None):
        self.seed = seed_string
        self.rules = production_rules
        self.meanings = meanings

    def _process_letter(self, letter):
        if letter in self.rules:
            rule_outcome = self.rules[letter]
            if isinstance(rule_outcome, (list, tuple)):
                if len(rule_outcome) == 2 and isinstance(rule_outcome[0], (list, tuple)) \
                        and isinstance(rule_outcome[1], (list, tuple)):
                    outcomes, weights = rule_outcome
                    return random.choices(outcomes, weights=weights, k=1)[0]
                else:
                    return random.choice(rule_outcome)
            else:
                return rule_outcome
        else:
            return letter

    @lru_cache()
    def get_generation(self, n: int) -> str:
        """
        Get the state of the system at the nth generation of iteration, where n=0 is the initial state. The first time
        a generation is requested, all previous generations must be processed; however, thereafter they are cached.

        :param n: which generation
        """
        if n < 0 or not isinstance(n, int):
            raise ValueError("Invalid LSystem generation; must be integer >= 0.")
        if n == 0:
            return self.seed
        return "".join(self._process_letter(letter) for letter in self.get_generation(n - 1))

    def get_generation_meanings(self, n: int) -> Tuple:
        """
        Get the meanings associated with the given generation, according to the meanings dictionary.

        :param n: which generation
        """
        if self.meanings is None:
            raise ValueError("Cannot get generation meanings; meanings were not defined for this LSystem.")
        return tuple(self.meanings[letter] for letter in self.get_generation(n))
