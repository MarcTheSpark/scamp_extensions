"""
Module containing functions for voicing a chord: given a set of pitch classes and a range to place them in,
these search the possible voicings and return whichever one best fits the preferences given, such as being
compactly spaced or centered in the range.
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
import numpy as np
from statistics import mean


#: Functions that score a voicing on some quality; the names are those accepted as spacing and range
#: preferences by :func:`chords_from_pitch_classes`. Each takes the pitches of a voicing and the
#: (min, max) range they were drawn from, and returns a score, higher being a better fit.
measurement_functions = {
    "uniqueness": lambda pitch_collection, _: len(set(p % 12 for p in pitch_collection)),
    "wide": lambda pitch_collection, _: max(pitch_collection) - min(pitch_collection),
    "compact": lambda pitch_collection, _: -(max(pitch_collection) - min(pitch_collection)),
    "even": lambda pitch_collection, _: -np.std(np.diff(sorted(pitch_collection))) if len(pitch_collection) > 2 else 1,
    "uneven": lambda pitch_collection, _: np.std(np.diff(sorted(pitch_collection))) if len(pitch_collection) > 2 else 1,
    "high": lambda pitch_collection, _: mean(pitch_collection),
    "low": lambda pitch_collection, _: mean(pitch_collection),
    "mid": lambda pitch_collection, pitch_range: -abs(mean(pitch_collection) - mean(pitch_range)),
}


def chords_from_pitch_classes(pcs, min_pitch, max_pitch, num_notes, prefer_unique_pcs=True,
                              spacing_and_range_prefs=("compact", "mid", "even"), how_many=1):
    """
    Find the voicings of the given pitch classes that best fit the given preferences. [AI WRITTEN DOC]

    :param pcs: the pitch classes (integers from 0 to 11) to voice
    :param min_pitch: lowest MIDI pitch the voicing may use
    :param max_pitch: highest MIDI pitch the voicing may use
    :param num_notes: how many notes the chord should have; capped at the number of pitches available
    :param prefer_unique_pcs: if True, prefer voicings that cover as many distinct pitch classes as possible,
        ahead of any of the other preferences
    :param spacing_and_range_prefs: the qualities to prefer in a voicing, in decreasing order of priority.
        These are keys of :data:`measurement_functions`: "wide"/"compact" (spread out or close together),
        "even"/"uneven" (equally or unequally spaced), and "high"/"low"/"mid" (placement within the range).
    :param how_many: how many voicings to return
    :return: a list of the best `how_many` voicings, each a tuple of MIDI pitches, best last
    """
    available_pitches = get_pcs_instances_in_range(pcs, min_pitch, max_pitch)
    pref_functions = ("uniqueness", ) + spacing_and_range_prefs if prefer_unique_pcs else spacing_and_range_prefs
    combos = sorted(itertools.combinations(available_pitches, min(num_notes, len(available_pitches))),
                    key=lambda pitches: tuple(measurement_functions[func_name](pitches, (min_pitch, max_pitch))
                                              for func_name in pref_functions))
    return combos[-how_many:]


def chord_from_pitch_classes(pcs, min_pitch, max_pitch, num_notes, prefer_unique_pcs=True,
                             spacing_and_range_prefs=("compact", "mid", "even")):
    """
    Find the single voicing of the given pitch classes that best fits the given preferences. See
    :func:`chords_from_pitch_classes`, of which this is the single-result version. [AI WRITTEN DOC]

    :param pcs: the pitch classes (integers from 0 to 11) to voice
    :param min_pitch: lowest MIDI pitch the voicing may use
    :param max_pitch: highest MIDI pitch the voicing may use
    :param num_notes: how many notes the chord should have; capped at the number of pitches available
    :param prefer_unique_pcs: if True, prefer voicings covering as many distinct pitch classes as possible
    :param spacing_and_range_prefs: the qualities to prefer, in decreasing order of priority
    :return: the best voicing, as a tuple of MIDI pitches
    """
    return chords_from_pitch_classes(pcs, min_pitch, max_pitch, num_notes, prefer_unique_pcs,
                                     spacing_and_range_prefs, how_many=1)[0]


def get_pcs_instances_in_range(pcs, min_pitch, max_pitch):
    """
    Every pitch within the given range belonging to one of the given pitch classes.

    :param pcs: the pitch classes (integers from 0 to 11) in question
    :param min_pitch: lowest MIDI pitch to consider (inclusive)
    :param max_pitch: highest MIDI pitch to consider (exclusive)
    """
    return [pitch for pitch in range(min_pitch, max_pitch) if pitch % 12 in pcs]
