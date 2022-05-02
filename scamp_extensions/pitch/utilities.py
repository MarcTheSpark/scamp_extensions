"""
Module containing pitch-related utility functions, such as those that convert between midi and hertz.
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

from typing import Sequence, Dict
from numbers import Real
from scamp_extensions.utilities.sequences import multi_option_function
import math


# ----------------------------------------------- Pitch Space Conversions ---------------------------------------------


@multi_option_function
def ratio_to_cents(ratio: Real) -> Real:
    """
    Given a frequency ratio, convert it to a corresponding number of cents.

    :param ratio: frequency ratio (e.g. 1.5 for a perfect fifth)
    """
    return math.log2(ratio) * 1200


@multi_option_function
def cents_to_ratio(cents: Real) -> Real:
    """
    Given a number of cents, convert it to a corresponding frequency ratio.

    :param cents: number of cents (e.g. 700 for a perfect fifth)
    """
    return math.pow(2, cents / 1200)


@multi_option_function
def midi_to_hertz(midi_value: Real, A: Real = 440) -> Real:
    """
    Given a MIDI pitch, returns the corresponding frequency in hertz.

    :param midi_value: a midi pitch (e.g. 60 for middle C)
    :param A: the tuning of A4 in hertz
    """
    return A * math.pow(2, (midi_value - 69) / 12)


@multi_option_function
def hertz_to_midi(hertz_value: Real, A: Real = 440) -> Real:
    """
    Given a frequency in hertz, returns the corresponding (floating point) MIDI pitch.

    :param hertz_value: a frequency in hertz
    :param A: the tuning of A4 in hertz
    """
    return 12 * math.log2(hertz_value / A) + 69


@multi_option_function
def freq_to_bark(f: Real) -> Real:
    """
    Converts a frequency in hertz to a (floating point) Bark number according to the psychoacoustic Bark scale
    (https://en.wikipedia.org/wiki/Bark_scale). This is a scale that compensates for the unevenness in human pitch
    acuity across our range of hearing. Here we use the function approximation proposed by Terhardt, which was chosen
    in part for its ease of inverse calculation.

    :param f: the input frequency
    """
    return 13.3 * math.atan(0.75*f/1000.0)


# the inverse formula
@multi_option_function
def bark_to_freq(b: Real) -> Real:
    """
    Converts a Bark number to its corresponding frequency in hertz. See :func:`freq_to_bark`.

    :param b: a (floating point) bark number
    """
    return math.tan(b/13.3)*1000.0/0.75


_pitch_class_displacements = {
    'c': 0,
    'd': 2,
    'e': 4,
    'f': 5,
    'g': 7,
    'a': 9,
    'b': 11
}

_accidental_displacements = {
    '#': 1,
    's': 1,
    'f': -1,
    'b': -1,
    'x': 2,
    'bb': -2
}


@multi_option_function
def note_name_to_number(note_name: str) -> int:
    """
    Converts a note name (e.g. "Bb5" or "C#2") to its corresponding MIDI number.

    :param note_name: The note name, e.g. "Bb5". The accidental can be any of "#", "s", "f", "b", "x", or "bb".
        Uses the convention of "C4" = 60.
    """
    note_name = note_name.lower().replace(' ', '')
    pitch_class_name = note_name[0]
    octave = note_name[-1]
    accidental = note_name[1:-1]
    return (int(octave) + 1) * 12 + \
           _pitch_class_displacements[pitch_class_name] + \
           (_accidental_displacements[accidental] if accidental in _accidental_displacements else 0)


# ----------------------------------------------------- Other ---------------------------------------------------------


def map_keyboard_to_microtonal_pitches(microtonal_pitches: Sequence[float],
                                       squared_penalty: bool = True) -> Dict[int, float]:
    """
    Given a list of microtonal (floating-point) MIDI pitches, finds an efficient map from keyboard-friendly (integer)
    pitches to the original microtonal pitches. This is really useful if you're trying to audition a microtonal
    collection on the keyboard and don't want to deal with making a mapping manually. Note: the code here is taken
    nearly verbatim from StackOverflow user `sacha` in response to this question:
    https://stackoverflow.com/questions/61825905/match-list-of-floats-to-nearest-integers-without-repeating

    :param microtonal_pitches: a collection of floating-point (microtonal) pitches
    :param squared_penalty: whether or not the choice is based on simple or squared error. (I.e. are we using taxicab
        or euclidean distance.)
    :return: a dictionary mapping keyboard-friendly (integer) pitches to the microtonal collection given
    """
    import math
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial.distance import cdist

    microtonal_pitches = np.array(microtonal_pitches)

    # hacky safety-net -> which candidates to look at
    min_ = math.floor(microtonal_pitches.min())
    max_ = math.ceil(microtonal_pitches.max())
    gap = max_ - min_

    cands = np.arange(min_ - gap, max_ + gap)

    cost_matrix = cdist(microtonal_pitches[:, np.newaxis], cands[:, np.newaxis])

    if squared_penalty:
        cost_matrix = np.square(cost_matrix)

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    solution = cands[col_ind]

    # cost would be computed like this:
    # `cost = cost_matrix[row_ind, col_ind].sum()`

    return {rounded_p: p for p, rounded_p in zip(microtonal_pitches, solution)}
