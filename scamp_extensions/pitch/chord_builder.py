import itertools
import numpy as np
from statistics import mean


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

    available_pitches = get_pcs_instances_in_range(pcs, min_pitch, max_pitch)
    pref_functions = ("uniqueness", ) + spacing_and_range_prefs if prefer_unique_pcs else spacing_and_range_prefs
    combos = sorted(itertools.combinations(available_pitches, min(num_notes, len(available_pitches))),
                    key=lambda pitches: tuple(measurement_functions[func_name](pitches, (min_pitch, max_pitch))
                                              for func_name in pref_functions))
    return combos[-how_many:]


def chord_from_pitch_classes(pcs, min_pitch, max_pitch, num_notes, prefer_unique_pcs=True,
                             spacing_and_range_prefs=("compact", "mid", "even")):
    return chords_from_pitch_classes(pcs, min_pitch, max_pitch, num_notes, prefer_unique_pcs,
                                     spacing_and_range_prefs, how_many=1)[0]


def get_pcs_instances_in_range(pcs, min_pitch, max_pitch):
    return [pitch for pitch in range(min_pitch, max_pitch) if pitch % 12 in pcs]
