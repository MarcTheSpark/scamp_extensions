"""
Subpackage containing mathematical utility functions (many of which are imported from :mod:`scamp.utilities`.
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

from scamp.utilities import is_x_pow_of_y, floor_x_to_pow_of_y, ceil_x_to_pow_of_y, round_x_to_pow_of_y, \
    floor_to_multiple, ceil_to_multiple, round_to_multiple, is_multiple, prime_factor, is_prime
from math import gcd
import math
from expenvelope import EnvelopeSegment
from numbers import Real


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)


def remap(value_or_values, out_min, out_max, in_min=None, in_max=None,
          input_warp="lin", output_warp="lin", clip=True):
    """
    Rescales the given value or values so that they fall within the given output range. Not efficient or vectorized,
    but unless you're using large datasets, that shouldn't be an issue.

    :param value_or_values: the vale or values to rescale
    :param out_min: lower bound of output range
    :param out_max: upper bound of output range
    :param in_min: lower bound of input range (defaults to minimum input value)
    :param in_max: upper bound of input range (defaults to maximum input value)
    :param input_warp: either "lin", or "exp" depending on whether the input values are linearly (e.g. pitch) or
        exponentially (e.g. frequency) spaced.
    :param output_warp: either "lin", "exp", or a number that corresponds to the shape of the warping curve. When using
        a number, 0 is linear, > 0 warps outputs towards the bottom of the range, and < 0 warps outputs towards the
        top of the range (see `~expenvelope.envelope.Envelope` for a description of `curve_shape`).
    :param clip: if True, clip output values so that they do not go outside of the designated output range
    :return: a suitable warped output value or list of output values
    """
    if not hasattr(value_or_values, '__len__'):
        if in_min is None or in_max is None:
            raise ValueError("When rescaling a single value, must supply in_min and in_max parameters.")
        return rescale([value_or_values], out_min, out_max, in_min, in_max, input_warp, output_warp)[0]

    if in_min is None:
        in_min = min(value_or_values)
    if in_max is None:
        in_max = max(value_or_values)

    if input_warp == "exp":
        log_in_min, log_in_max = math.log(in_min), math.log(in_max)
        log_in_range = log_in_max - log_in_min
        normalized_data = [(math.log(x) - log_in_min) / log_in_range
                           for x in value_or_values]
    else:
        in_range = in_max - in_min
        normalized_data = [(x - in_min) / in_range for x in value_or_values]

    if clip:
        normalized_data = [min(max(x, 0), 1) for x in normalized_data]

    if output_warp == "exp":
        log_out_min, log_out_max = math.log(out_min), math.log(out_max)
        log_out_range = log_out_max - log_out_min
        return [math.exp(log_out_min + log_out_range * x) for x in normalized_data]
    elif isinstance(output_warp, Real):
        warp_envelope = EnvelopeSegment(0, 1, out_min, out_max, output_warp)
        return [warp_envelope.value_at(x) for x in normalized_data]
    else:
        out_range = out_max - out_min
        return [out_min + out_range * x for x in normalized_data]
