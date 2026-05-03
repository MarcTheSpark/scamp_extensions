"""
Module containing the :func:`boolean_streamer` decorator, which converts a boolean-yielding generator into a
:class:`BooleanStreamer` object. :class:`BooleanStreamer` objects are iterable and can be combined using the `&`,
`|` and `~` operators to compose more complex streams of booleans. A few useful decorated boolean_streamer functions
are given, including the :func:`SieveStreamer`, which implements Xenakis-style sieves the :func:`RandStreamer`, which
generates weighted random `True`/`False` values, and the :func:`FreqStreamer` which generates regularly spaced `True`'s
at the frequency defined by the function.
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

import inspect
import random
from functools import wraps


class BooleanStreamer:
    """
    Wrapper for a generator function that returns only boolean values. By wrapping it as a BooleanStreamer, it can
    be combined with other BooleanStreamers using the `&`, `|` and `~` operators.

    :param generator_function: a boolean-yielding generator function
    """

    def __init__(self, generator_function, *args, **kwargs):
        if isinstance(generator_function, BooleanStreamer):
            # if we pass in a BooleanStreamer, just make a copy of it; don't nest
            self.generator_function = generator_function.generator_function
            self.args = generator_function.args if len(args) == 0 else args
            self.kwargs = generator_function.kwargs if len(kwargs) == 0 else kwargs
        elif not inspect.isgeneratorfunction(generator_function):
            # otherwise, generator_function had better be a generator function
            raise ValueError("A BooleanStreamer can only be created for a generator function")
        else:
            self.generator_function = generator_function
            self.args = args
            self.kwargs = kwargs

    def __call__(self):
        return iter(self)

    def __iter__(self):
        return self.generator_function(*self.args, **self.kwargs)

    def __and__(self, other):
        if not isinstance(other, BooleanStreamer):
            raise ValueError("BoolStreamers can only be combined with other BoolStreamers")

        def combined_generator_func():
            for x, y in zip(self, other):
                yield x and y

        return BooleanStreamer(combined_generator_func)

    def __or__(self, other):
        if not isinstance(other, BooleanStreamer):
            raise ValueError("BoolStreamers can only be combined with other BoolStreamers")

        def combined_generator_func():
            for x, y in zip(self, other):
                yield x or y

        return BooleanStreamer(combined_generator_func)

    def __invert__(self):

        def inverted_generator_func():
            for x in self:
                yield not x

        return BooleanStreamer(inverted_generator_func)

    def __repr__(self):
        return f"BooleanStreamer({self.generator_function})"


def boolean_streamer(func):
    """
    Decorator that converts a boolean-yielding generator function into a :class:`BooleanStreamer` object
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        return BooleanStreamer(func, *args, **kwargs)

    return wrapper


@boolean_streamer
def SieveStreamer(modulo, shift=0):
    """
    A Xenakis-sieve-style :class:`BooleanStreamer` that yields patterns of True/False based on a modulo, which defines
    the cycle length; and a shift, which defines which remainder (or remainders) yielding True values.

    :param modulo: cycle length
    :param shift: which remainders yield `True`
    """
    i = 0
    shift = (shift,) if not hasattr(shift, '__len__') else tuple(shift)
    while True:
        yield any((i - s) % modulo == 0 for s in shift)
        i += 1


@boolean_streamer
def RandStreamer(true_prob):
    """
    A :class:`BooleanStreamer` that yields True values with the given probability.

    :param true_prob: probability of a True value
    """
    while True:
        yield random.random() < true_prob


@boolean_streamer
def FreqStreamer(freq_func):
    """
    A phase-accumulation based :class:`BooleanStreamer` that yields True values with a frequency given by the
    frequency function.

    :param freq_func: a callable that takes an index as an input and return the phase accumulation for that index.
        Super transparent, I know.
    """
    i = phase = 0
    while True:
        phase += freq_func(i)
        if phase > 1:
            yield True
            phase = phase % 1
        else:
            yield False
        i += 1
