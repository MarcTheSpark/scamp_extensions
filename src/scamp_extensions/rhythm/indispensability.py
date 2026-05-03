"""
Re-implementation and extension of Clarence Barlow's concept of rhythmic indispensability such that it works for
additive meters (even nested additive meters). Since these are my own extensions of Barlow's ideas, they are here
instead of in :mod:`scamp_extensions.composers.barlicity`.
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

from numbers import Real
from typing import List, Union, Sequence
from .metric_structure import MeterArithmeticGroup, INT_OR_FLOAT


def indispensability_array_from_expression(meter_arithmetic_expression: str, normalize: bool = False,
                                           break_up_large_numbers: bool = False,
                                           upbeats_before_group_length: bool = True) -> List[INT_OR_FLOAT]:
    """
    Generates an array of indispensability values for a meter and subdivision, as expressed by a meter arithmetic
    expression. Such expressions allow great flexibility in describing metric structure, making possible additive,
    multiplicative, and hybrid metrical structures.

    :param meter_arithmetic_expression: An string expression representing a metric hierarchy (meter and subdivision
        structure). For instance, "2 * 3" would create the eighth-note subdivisions of 6/8, and "2 + 3 + 2" would create
        an additive meter (2+3+2)/8.  "(2 + 3 + 2) * 3" would create a kind of hybrid of these: seven main beats in a
        2 + 3 + 2 pattern, each of which is subdivided in 3. This might be notated as 6/8+9/8+6/8.
    :param normalize: if True, indispensabilities range from 0 to 1. If false, they count up from 0.
    :param break_up_large_numbers: if True, numbers greater than 3 are broken up into a sum of 2's
        followed by one 3 if odd. This is the Barlow approach.
    :param upbeats_before_group_length: see description in :func:`metric_structure.flatten_beat_groups`. Affects the
        result when there are groups of uneven length at some level of metric structure. To achieve the standard
        Barlowian result, set this to False. I think it works better as True, though.
    :return: a list of indispensabilities for the pulses of the given meter.
    """
    return MeterArithmeticGroup.parse(meter_arithmetic_expression) \
        .to_metric_structure(break_up_large_numbers) \
        .get_indispensability_array(normalize=normalize, upbeats_before_group_length=upbeats_before_group_length)


def indispensability_array_from_strata(*rhythmic_strata: Union[int, Sequence[int]], normalize: bool = False,
                                       break_up_large_numbers: bool = False,
                                       upbeats_before_group_length: bool = True) -> List[INT_OR_FLOAT]:
    """
    Alternate implementation of :func:`~scamp_extensions.composers.barlicity.get_indispensability_array`, leveraging
    the :class:`~scamp_extensions.rhythm.metric_structure.MetricStructure` class to do the calculations.

    :param rhythmic_strata: can be either tuples, representing additive metric layers, or integers, representing simple
        metric layers.
    :param normalize: if True, indispensabilities range from 0 to 1. If false, they count up from 0.
    :param break_up_large_numbers: if True, numbers greater than 3 are broken up into a sum of 2's
        followed by one 3 if odd. This is the Barlow approach.
    :param upbeats_before_group_length: see description in :func:`metric_structure.flatten_beat_groups`. Affects the
        result when there are groups of uneven length at some level of metric structure. To achieve the standard
        Barlowian result, set this to False. I think it works better as True, though.
    :return: a list of indispensabilities for the pulses of the given meter.
    """
    expression = "*".join(
        ("("+"+".join(str(y) for y in x)+")" if hasattr(x, "__len__") else str(x)) for x in rhythmic_strata
    )
    return indispensability_array_from_expression(
        expression, normalize=normalize, break_up_large_numbers=break_up_large_numbers,
        upbeats_before_group_length=upbeats_before_group_length
    )


def barlow_style_indispensability_array(*rhythmic_strata: Union[int, Sequence[int]],
                                        normalize: bool = False) -> List[INT_OR_FLOAT]:
    """
    Alternate implementation of :func:`~scamp_extensions.composers.barlicity.get_standard_indispensability_array`,
    leveraging the :class:`~scamp_extensions.rhythm.metric_structure.MetricStructure` class to do the calculations.

    :param rhythmic_strata: can be either tuples, representing additive metric layers, or integers, representing simple
        metric layers.
    :param normalize: if True, indispensabilities range from 0 to 1. If false, they count up from 0.
    :return: a list of indispensabilities for the pulses of the given meter.
    """
    if not all(isinstance(x, int) for x in rhythmic_strata):
        raise ValueError("Standard Barlow indispensability arrays must be based on from integer strata.")
    return indispensability_array_from_expression("*".join(str(x) for x in rhythmic_strata), normalize=normalize,
                                                  break_up_large_numbers=True, upbeats_before_group_length=False)
