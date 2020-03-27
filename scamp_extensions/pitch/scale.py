from expenvelope import Envelope
import math
from numbers import Real
from scamp.utilities import SavesToJSON
import logging
from copy import deepcopy
from .interval import PitchInterval


class ScaleType(SavesToJSON):

    standard_equal_tempered_patterns = {
        "diatonic": [200., 400., 500., 700., 900., 1100., 1200.],
        "melodic minor": [200., 300., 500., 700., 900., 1100., 1200.],
        "harmonic minor": [200., 300., 500., 700., 800., 1100., 1200.],
        "whole tone": [200., 400., 600., 800., 1000., 1200.],
        "octatonic": [200., 300., 500., 600., 800., 900., 1100., 1200.]
    }

    def __init__(self, *intervals):
        """
        A ScaleType represents the intervallic relationships in a scale without specifying a specific starting point.
        This maps closely to what is represented in a Scala .scl file, which is why this object can load from and
        save to that format. In fact, the one difference between the data stored here and that stored in a .scl file is
        that this object allows a scale degree to be defined by both a cents offset and a subsequently applied ratio.

        :param intervals: a sequence of PitchIntervals above the starting note. Alternatively, an element can simply be
            a type of data that PitchInterval can parse.
        """
        self.intervals = [x if isinstance(x, PitchInterval) else PitchInterval.parse(x) for x in intervals]

    def to_half_steps(self):
        return [interval.to_half_steps() for interval in self.intervals]

    def rotate(self, steps, in_place=True):
        intervals = self.intervals if in_place else deepcopy(self.intervals)
        steps = steps % len(intervals)

        if steps == 0:
            rotated_intervals = intervals
        else:
            shift_first_intervals_up = intervals[steps:] + [x + intervals[-1] for x in intervals[:steps]]
            rotated_intervals = [x - intervals[steps - 1] for x in shift_first_intervals_up]

        if in_place:
            self.intervals = rotated_intervals
            return self
        else:
            return ScaleType(*rotated_intervals)

    # ------------------------------------- Class Methods ---------------------------------------

    @classmethod
    def diatonic(cls, modal_shift: int = 0):
        return cls(*ScaleType.standard_equal_tempered_patterns["diatonic"]).rotate(modal_shift)

    major = ionian = diatonic

    @classmethod
    def dorian(cls): return cls.diatonic(1)

    @classmethod
    def phrygian(cls): return cls.diatonic(2)

    @classmethod
    def lydian(cls): return cls.diatonic(3)

    @classmethod
    def mixolydian(cls): return cls.diatonic(4)

    @classmethod
    def aeolian(cls): return cls.diatonic(5)

    natural_minor = aeolian

    @classmethod
    def locrian(cls): return cls.diatonic(6)

    @classmethod
    def whole_tone(cls):
        return cls(*ScaleType.standard_equal_tempered_patterns["whole tone"])

    @classmethod
    def octatonic(cls, whole_step_first=True):
        if whole_step_first:
            return cls(*ScaleType.standard_equal_tempered_patterns["octatonic"])
        else:
            return cls(*ScaleType.standard_equal_tempered_patterns["octatonic"]).rotate(1)

    # ------------------------------------- Loading / Saving ---------------------------------------

    def save_to_scala(self, file_path, description="Mystery scale saved using SCAMP"):
        lines = ["! {}".format(file_path.split("/")[-1]),
                 "!",
                 "{}".format(description),
                 str(len(self.intervals)),
                 "!"]
        lines.extend(interval.to_scala_string() for interval in self.intervals)
        with open(file_path, "w") as scala_file:
            scala_file.write("\n".join(lines))

    @classmethod
    def load_from_scala(cls, file_path):
        pitch_entries = []
        with open(file_path, "r") as scala_file:
            lines = scala_file.read().split("\n")
            description = num_steps = None
            for line in lines:
                line = line.strip()
                if line.startswith("!") or len(line) == 0:
                    continue
                elif description is None:
                    description = line
                elif num_steps is None:
                    num_steps = int(line)
                else:
                    first_non_numeric_char = None
                    for i, char in enumerate(line):
                        if not (char.isnumeric() or char in (".", "/")):
                            first_non_numeric_char = i
                            break
                    if first_non_numeric_char is None:
                        pitch_entries.append(line)
                    else:
                        pitch_entries.append(line[:i])
            if len(pitch_entries) != num_steps:
                logging.warning("Wrong number of pitches in Scala file. "
                                "That's fine, I guess, but though you should know...")
        return cls(*pitch_entries)

    def _to_json(self):
        return [interval. _to_json() for interval in self.intervals]

    @classmethod
    def _from_json(cls, json_list):
        return cls(*json_list)

    def __repr__(self):
        return "ScaleType({})".format(self.intervals)


class Scale(SavesToJSON):

    def __init__(self, scale_type: ScaleType, start_pitch: Real, cycle=True):
        self.scale_type = scale_type
        self.start_pitch = start_pitch
        # convert the scale type to a list of MIDI-valued seed pitches
        self._seed_pitches = (start_pitch, ) + tuple(start_pitch + x for x in self.scale_type.to_half_steps())
        self._envelope = Envelope.from_points(*zip(range(len(self._seed_pitches)), self._seed_pitches))
        self._inverse_envelope = Envelope.from_points(*zip(self._seed_pitches, range(len(self._seed_pitches))))
        self.cycle = cycle
        self.num_steps = len(self._seed_pitches) - 1
        self.width = self._seed_pitches[-1] - self._seed_pitches[0] if cycle else None

    @classmethod
    def from_pitches(cls, seed_pitches, cycle=True):
        return cls(ScaleType(*(100. * (x - seed_pitches[0]) for x in seed_pitches[1:])), seed_pitches[0], cycle=cycle)

    @classmethod
    def from_scala_file(cls, file_path, start_pitch, cycle=True):
        return cls(ScaleType.load_from_scala(file_path), start_pitch, cycle=cycle)

    @classmethod
    def from_start_pitch_and_cent_or_ratio_intervals(cls, start_pitch, intervals, cycle=True):
        return cls(ScaleType(*intervals), start_pitch, cycle=cycle)

    def degree_to_pitch(self, degree):
        if self.cycle:
            cycle_displacement = math.floor(degree / self.num_steps)
            mod_degree = degree % self.num_steps
            return self._envelope.value_at(mod_degree) + cycle_displacement * self.width
        else:
            return self._envelope.value_at(degree)

    def pitch_to_degree(self, pitch):
        if self.cycle:
            cycle_displacement = math.floor((pitch - self._seed_pitches[0]) / self.width)
            mod_pitch = (pitch - self._seed_pitches[0]) % self.width + self._seed_pitches[0]
            return self._inverse_envelope.value_at(mod_pitch) + cycle_displacement * self.num_steps
        else:
            return self._inverse_envelope.value_at(pitch)

    def round(self, pitch):
        return self.degree_to_pitch(round(self.pitch_to_degree(pitch)))

    def floor(self, pitch):
        return self.degree_to_pitch(math.floor(self.pitch_to_degree(pitch)))

    def ceil(self, pitch):
        return self.degree_to_pitch(math.ceil(self.pitch_to_degree(pitch)))

    # ------------------------------------- Class Methods ---------------------------------------

    @classmethod
    def diatonic(cls, start_pitch, modal_shift: int = 0, cycle=True):
        return cls(ScaleType.diatonic(modal_shift), start_pitch, cycle=cycle)

    major = ionian = diatonic

    @classmethod
    def dorian(cls, start_pitch, cycle=True): return cls(ScaleType.dorian(), start_pitch, cycle=cycle)

    @classmethod
    def phrygian(cls, start_pitch, cycle=True): return cls(ScaleType.phrygian(), start_pitch, cycle=cycle)

    @classmethod
    def lydian(cls, start_pitch, cycle=True): return cls(ScaleType.lydian(), start_pitch, cycle=cycle)

    @classmethod
    def mixolydian(cls, start_pitch, cycle=True): return cls(ScaleType. mixolydian(), start_pitch, cycle=cycle)

    @classmethod
    def aeolian(cls, start_pitch, cycle=True): return cls(ScaleType.aeolian(), start_pitch, cycle=cycle)

    natural_minor = aeolian

    @classmethod
    def locrian(cls, start_pitch, cycle=True): return cls(ScaleType.locrian(), start_pitch, cycle=cycle)

    @classmethod
    def whole_tone(cls, start_pitch, cycle=True): return cls(ScaleType.whole_tone(), start_pitch, cycle=cycle)

    @classmethod
    def octatonic(cls, start_pitch, cycle=True, whole_step_first=True):
        return cls(ScaleType.octatonic(whole_step_first=whole_step_first), start_pitch, cycle=cycle)

    # ------------------------------------- Loading / Saving ---------------------------------------

    def  _to_json(self):
        return {
            "scale_type": self.scale_type. _to_json(),
            "start_pitch": self.start_pitch,
            "cycle": self.cycle
        }

    @classmethod
    def _from_json(cls, json_object):
        json_object["scale_type"] = ScaleType. _from_json(json_object["scale_type"])
        return cls(**json_object)

    # ------------------------------------- Special Methods ---------------------------------------

    def __iter__(self):
        for step_num in range(self.num_steps + 1):
            yield self.degree_to_pitch(step_num)

    def __repr__(self):
        return "Scale({}, {}{})".format(
            repr(self.scale_type),
            self.start_pitch,
            ", cycle={}".format(self.cycle) if self.cycle is not True else ""
        )
