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


class LSystem:
    """
    Simple implementation of an LSystem. Each generation is a string consisting of an alphabet of characters.
    Optionally, these characters can be assigned meanings.

    :param seed_string: the initial string
    :param evolution_rules: dictionary describing how each letter evolves in a subsequent generation. Any letter
        not found in the dictionary is assumed to be a constant
    :param meanings: (optional) dictionary specifying the meaning of each letter. Should contain an entry for every
        letter potentially encountered.
    :ivar seed: the initial string
    :ivar rules: dictionary describing how each letter evolves in a subsequent generation. Any letter
        not found in the dictionary is assumed to be a constant
    :ivar meanings: (optional) dictionary specifying the meaning of each letter. Should contain an entry for every
        letter potentially encountered.
    """

    def __init__(self, seed_string: str, evolution_rules: MutableMapping[str, str],
                 meanings: MutableMapping[str, Any] = None):
        self.seed = seed_string
        self.rules = evolution_rules
        self.meanings = meanings

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
        return "".join(self.rules.get(letter, letter) for letter in self.get_generation(n - 1))

    def get_generation_meanings(self, n: int) -> Tuple:
        """
        Get the meanings associated with the given generation, according to the meanings dictionary.

        :param n: which generation
        """
        if self.meanings is None:
            raise ValueError("Cannot get generation meanings; meanings were not defined for this LSystem.")
        return tuple(self.meanings[letter] for letter in self.get_generation(n))
