from expenvelope import Envelope
import itertools
import math
from fractions import Fraction
from scamp.utilities import SavesToJSON
from ..utils import ratio_to_cents
import logging
from typing import Union


class PitchInterval:

    def __init__(self, cents: float, ratio: Union[Fraction, int]):
        self.cents = cents
        self.ratio = ratio

    @classmethod
    def parse(cls, representation):
        if isinstance(representation, str):
            if "," in representation:
                cents_string, ratio_string = representation.split(",")
                return cls(float(cents_string))
            elif "/" in representation:
                return cls(0, Fraction(representation))
            else:

                return cls.parse(eval(representation))
        elif isinstance(data, (int, float, Fraction)):
            return data
        elif hasattr(data, "__len__"):
            return tuple(ScaleType._interpret_step_data(x) for x in data)
        else:
            return float(data)

    def to_cents(self):
        return self.cents + ratio_to_cents(self.ratio)

    def to_half_steps(self):
        return self.to_cents() / 100

    def __repr__(self):
        return "PitchInterval({}, {})".format(self.cents, self.ratio)


class ScaleType(SavesToJSON):

    def __init__(self, *scale_degree_intervals):
        """
        A ScaleType represents the intervallic relationships in a scale without specifying a specific starting point.
        This maps closely to what is represented in a Scala .scl file, which is why this object can load from and
        save to that format. In fact the one difference between the data stored here and that stored in a .scl file is
        that this object allows a scale degree to be defined by both a cents offset and a subsequently applied ratio.

        :param scale_degree_intervals: a sequence of intervals above the starting note. Each element should be either:
            - a float (representing cents)
            - an int or a Fraction object (representing a ratio)
            - a tuple of (cents, ratio)
            - a string, which will be evaluated as a (cents, ratio) tuple if it has a comma, and will be evaluated as
            a Fraction if it has a slash. e.g. "3" is a ratio, "37." is cents, "4/3" is a ratio, and "200., 5/4"
            is a cents displacement followed by a ratio.
        """
        self.scale_degree_intervals = ScaleType._interpret_step_data(scale_degree_intervals)
        # check that the data is okay
        for interval in self.scale_degree_intervals:
            if not isinstance(interval, (tuple, int, float, Fraction)) or \
                    (isinstance(interval, tuple) and not len(interval) == 2
                     and isinstance(interval[1], (int, Fraction))):
                raise ValueError("Each scale degree must be either a number of cents (float), a frequency ratio (int "
                                 "or fraction), or a 2-tuple combining a number of cents and a frequency ratio.")

    @staticmethod
    def _interpret_step_data(data):
        if isinstance(data, str):
            if "," in data:
                return ScaleType._interpret_step_data(data.split(","))
            elif "/" in data:
                return Fraction(data)
            else:
                return eval(data)
        elif isinstance(data, (int, float, Fraction)):
            return data
        elif hasattr(data, "__len__"):
            return tuple(ScaleType._interpret_step_data(x) for x in data)
        else:
            return float(data)

    def to_half_steps(self):
        half_steps = []
        for interval in self.scale_degree_intervals:
            if hasattr(interval, "__len__"):
                cents, ratio = interval
            elif isinstance(interval, (int, Fraction)):
                cents, ratio = 0., interval
            else:
                cents, ratio = interval, 1
            half_steps.append((cents + ratio_to_cents(ratio)) / 100)
        return half_steps

    def save_to_scala(self, file_path, description="Mystery scale saved using SCAMP"):
        lines = ["! {}".format(file_path.split("/")[-1]),
                 "!",
                 "{}".format(description),
                 str(len(self.scale_degree_intervals)),
                 "!"]
        for interval in self.scale_degree_intervals:
            if isinstance(interval, tuple):
                cents, ratio = interval
                lines.append(str(float((cents + ratio_to_cents(ratio)))))
            else:
                lines.append(str(interval))
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

    def to_json(self):
        json_list = []
        for scale_degree in self.scale_degree_intervals:
            if isinstance(scale_degree, (float, int)):
                json_list.append(scale_degree)
            elif isinstance(scale_degree, Fraction):
                json_list.append(str(scale_degree.numerator) + "/" + str(scale_degree.denominator))
            elif isinstance(scale_degree, tuple):
                json_list.append((float(scale_degree[0]),
                                  str(scale_degree[1].numerator) + "/" + str(scale_degree[1].denominator)
                                  if isinstance(scale_degree[1], Fraction) else scale_degree[1]))
            else:
                # handle any other Real number type
                json_list.append(float(scale_degree))
        return json_list

    @classmethod
    def from_json(cls, json_list):
        return cls(*json_list)

    def __str__(self):
        return "ScaleType({})".format(self.scale_degree_intervals)

# Change Scale class so that it takes a ScaleClass object and a start pitch as well as the cyclic argument


class Scale:
    _standard_patterns = {
        "diatonic": [2, 2, 1, 2, 2, 2, 1],
        "melodic minor": [2, 1, 2, 2, 2, 2, 1],
        "harmonic minor": [2, 1, 2, 2, 1, 3, 1]
    }

    # def __init__(self, seed_pitches, cyclic=True):
    #     if not (len(seed_pitches) > 1 and all(a < b for a, b in zip(seed_pitches[:-1], seed_pitches[1:]))):
    #         raise ValueError("Scale seed must be a list of two or more pitches in ascending order")
    #     self._envelope = Envelope.from_points(*zip(range(len(seed_pitches)), seed_pitches))
    #     self._inverse_envelope = Envelope.from_points(*zip(seed_pitches, range(len(seed_pitches))))
    #     self._cycle_length = len(seed_pitches) - 1 if cyclic else None
    #     self._cycle_interval = seed_pitches[-1] - seed_pitches[0] if cyclic else None
    #     self._seed_pitches = seed_pitches

    def __init__(self, scale_type, start_pitch, cyclic=True):
        pass

    @classmethod
    def from_pitches(cls, seed_pitches, cyclic=True):
        pass

    @classmethod
    def from_scala_file(cls, file_path, start_pitch, cyclic=True):
        pass

    @classmethod
    def from_start_pitch_and_intervals(cls, start_pitch, intervals, cyclic=True):
        pass


    def degree_to_pitch(self, degree):
        if self._cycle_length is not None:
            cycle_displacement = math.floor(degree / self._cycle_length)
            mod_degree = degree % self._cycle_length
            return self._envelope.value_at(mod_degree) + cycle_displacement * self._cycle_interval
        else:
            return self._envelope.value_at(degree)

    def pitch_to_degree(self, pitch):
        if self._cycle_length is not None:
            cycle_displacement = math.floor((pitch - self._seed_pitches[0]) / self._cycle_interval)
            mod_pitch = (pitch - self._seed_pitches[0]) % self._cycle_interval + self._seed_pitches[0]
            return self._inverse_envelope.value_at(mod_pitch) + cycle_displacement * self._cycle_length
        else:
            return self._inverse_envelope.value_at(pitch)

    def round(self, pitch):
        return self.degree_to_pitch(round(self.pitch_to_degree(pitch)))

    def floor(self, pitch):
        return self.degree_to_pitch(math.floor(self.pitch_to_degree(pitch)))

    def ceil(self, pitch):
        return self.degree_to_pitch(math.ceil(self.pitch_to_degree(pitch)))

    # ------------------------------------- CLASS METHODS ---------------------------------------

    @classmethod
    def from_frequency_ratios(cls, start_pitch):
        pass

    @staticmethod
    def _shift_scale_pattern(pattern, shift):
        if not isinstance(shift, int):
            raise ValueError("Shift must be an integer.")
        shift = shift % len(pattern)
        return pattern[shift:] + pattern[:shift]

    @classmethod
    def from_start_pitch_and_intervals(cls, start_pitch, intervals, cyclic=True):
        return Scale([start_pitch] + [start_pitch + x for x in itertools.accumulate(intervals)], cyclic=cyclic)

    @classmethod
    def diatonic(cls, start_pitch, modal_shift=0):
        return cls.from_start_pitch_and_intervals(
            start_pitch, Scale._shift_scale_pattern(Scale._standard_patterns["diatonic"], modal_shift))

    ionian = major = diatonic

    @classmethod
    def dorian(cls, start_pitch): return cls.diatonic(start_pitch, 1)

    @classmethod
    def harmonic_minor(cls, start_pitch, modal_shift=0):
        return cls.from_start_pitch_and_intervals(
            start_pitch, Scale._shift_scale_pattern(Scale._standard_patterns["harmonic minor"], modal_shift))

    @classmethod
    def melodic_minor_ascending(cls, start_pitch, modal_shift=0):
        return cls.from_start_pitch_and_intervals(
            start_pitch, Scale._shift_scale_pattern(Scale._standard_patterns["melodic minor"], modal_shift))

    @classmethod
    def acoustic(cls, start_pitch, modal_shift=0):
        return cls.melodic_minor_ascending(start_pitch, modal_shift + 3)
