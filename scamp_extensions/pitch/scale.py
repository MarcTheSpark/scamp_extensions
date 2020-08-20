"""
Module containing classes for flexibly representing musical scales. This includes the :class:`PitchInterval` class, for
representing just and/or equal-tempered intervals; the :class:`ScaleType` class, which represents a succession of
intervals without specifying a starting point; and the :class:`Scale` class, which combines a ScaleType with a
starting reference pitch, and also allows for a choice between cyclical and non-cyclical.
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

from fractions import Fraction
from typing import Sequence

from expenvelope.envelope import Envelope, SavesToJSON
from .utilities import ratio_to_cents
import math
from numbers import Real
import logging
from copy import deepcopy


class PitchInterval(SavesToJSON):

    """
    Represents an interval between two pitches. This combines a cents displacement and a frequency ratio, allowing
    it to represent both just and equal-tempered intervals, or even a combination of both. PitchIntervals can be
    added, negated, and subtracted.

    :param cents: cents displacement
    :param ratio: frequency ratio, either instead of or in addition to the cents displacement
    """

    def __init__(self, cents: float, ratio: Fraction):
        self.cents = cents
        self.ratio = ratio

    @classmethod
    def parse(cls, representation):
        """
        Parses several different possible types of data into a PitchInterval object.

        :param representation: One of the following:
            - a float (representing cents)
            - an int or a Fraction object (representing a ratio)
            - a tuple of (cents, ratio)
            - a string, which will be evaluated as a (cents, ratio) tuple if it has a comma, and will be evaluated as
            a Fraction if it has a slash. e.g. "3" is a ratio, "37." is cents, "4/3" is a ratio, and "200., 5/4"
            is a cents displacement followed by a ratio.
        :return: a PitchInterval
        """
        if isinstance(representation, dict):
            return cls._from_json(representation)
        elif isinstance(representation, str):
            if "," in representation:
                cents_string, ratio_string = representation.split(",")
                return cls(float(cents_string), Fraction(ratio_string))
            elif "/" in representation:
                return cls(0, Fraction(representation))
            else:
                return cls.parse(eval(representation))
        elif hasattr(representation, "__len__"):
            return cls(float(representation[0]), Fraction(representation[1]))
        elif isinstance(representation, float):
            return cls(representation, Fraction(1))
        elif isinstance(representation, (int, Fraction)):
            return cls(0., Fraction(representation))
        else:
            raise ValueError("Cannot parse given representation as a pitch interval.")

    def to_cents(self) -> float:
        """
        Resolves this interval to its size in cents.
        """
        return self.cents + ratio_to_cents(self.ratio)

    def to_half_steps(self) -> float:
        """
        Resolves this interval to its size in half steps.
        """
        return self.to_cents() / 100

    def to_scala_string(self):
        """
        Returns a string representation of this interval for use in exporting to scala files. Scala intervals can be
        either in cents or frequency ratio, however, unlike :class:`PitchInterval`, they cannot combine the two. Thus,
        if this PitchInterval combines the two, it will be converted to a flat cents value.
        """
        if self.cents == 0 and self.ratio == 1:
            return "0."
        elif self.cents == 0:
            return str(self.ratio)
        elif self.ratio == 1:
            return str(self.cents)
        else:
            return str(self.to_cents())

    # ------------------------------------- Loading / Saving ---------------------------------------

    def _to_dict(self):
        return {"cents": self.cents, "ratio": [self.ratio.numerator, self.ratio.denominator]}

    @classmethod
    def _from_dict(cls, json_dict):
        json_dict["ratio"] = Fraction(*json_dict["ratio"])
        return cls(**json_dict)

    def __neg__(self):
        return PitchInterval(-self.cents, 1/self.ratio)

    def __add__(self, other):
        if not isinstance(other, PitchInterval):
            raise ValueError("PitchIntervals can only be added or subtracted from other PitchIntervals.")
        return PitchInterval(self.cents + other.cents, self.ratio * other.ratio)

    def __sub__(self, other):
        return self + -other

    def __repr__(self):
        return "PitchInterval({}, {})".format(self.cents, self.ratio)


class ScaleType(SavesToJSON):
    """
    A ScaleType represents the intervallic relationships in a scale without specifying a specific starting point.
    This maps closely to what is represented in a Scala .scl file, which is why this object can load from and
    save to that format. In fact, the one difference between the data stored here and that stored in a .scl file is
    that this object allows a scale degree to be defined by both a cents offset and a subsequently applied ratio.

    :param intervals: a sequence of intervals above the starting note. These can be either :class:`PitchInterval`
        objects or anything that can be interpreted by :func:`PitchInterval.parse`.
    """

    _standard_equal_tempered_patterns = {
        "chromatic": [100.],
        "diatonic": [200., 400., 500., 700., 900., 1100., 1200.],
        "melodic minor": [200., 300., 500., 700., 900., 1100., 1200.],
        "harmonic minor": [200., 300., 500., 700., 800., 1100., 1200.],
        "whole tone": [200., 400., 600., 800., 1000., 1200.],
        "octatonic": [200., 300., 500., 600., 800., 900., 1100., 1200.]
    }

    def __init__(self, *intervals):
        self.intervals = [x if isinstance(x, PitchInterval) else PitchInterval.parse(x) for x in intervals]

    def to_half_steps(self) -> Sequence[float]:
        """
        Returns a list of floats representing the number of half steps from the starting pitch for each scale degree.
        """
        return [interval.to_half_steps() for interval in self.intervals]

    def rotate(self, steps: int, in_place: bool = True) -> 'ScaleType':
        """
        Rotates the step sizes of this scale type in the manner of a modal shift. E.g. going from ionian to lydian
        would be a rotation of 3.

        :param steps: the number of steps to shift the starting point of the scale up or down by. Can be negative.
        :param in_place: whether to modify this ScaleType in place, or to return a modified copy.
        :return: the modified ScaleType
        """
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
    def chromatic(cls):
        """Returns a 12-tone equal tempered chromatic ScaleType."""
        return cls(*ScaleType._standard_equal_tempered_patterns["chromatic"])

    @classmethod
    def diatonic(cls, modal_shift: int = 0) -> 'ScaleType':
        """
        Returns a diatonic ScaleType with the specified modal shift.

        :param modal_shift: how many steps up or down to shift the starting note of the scale. 0 returns ionian,
            1 returns dorian, 2 returns phrygian, etc. (There are also convenience methods for creating these
            modal scale types.)
        """
        return cls(*ScaleType._standard_equal_tempered_patterns["diatonic"]).rotate(modal_shift)

    @classmethod
    def major(cls, modal_shift: int = 0) -> 'ScaleType':
        """Alias of :func:`ScaleType.diatonic`."""
        return cls.diatonic(modal_shift)

    @classmethod
    def ionian(cls, modal_shift: int = 0) -> 'ScaleType':
        """Alias of :func:`ScaleType.diatonic`."""
        return cls.diatonic(modal_shift)

    @classmethod
    def dorian(cls) -> 'ScaleType':
        """Convenience method for creating a dorian ScaleType."""
        return cls.diatonic(1)

    @classmethod
    def phrygian(cls) -> 'ScaleType':
        """Convenience method for creating a phrygian ScaleType."""
        return cls.diatonic(2)

    @classmethod
    def lydian(cls) -> 'ScaleType':
        """Convenience method for creating a lydian ScaleType."""
        return cls.diatonic(3)

    @classmethod
    def mixolydian(cls) -> 'ScaleType':
        """Convenience method for creating a myxolydian ScaleType."""
        return cls.diatonic(4)

    @classmethod
    def aeolian(cls) -> 'ScaleType':
        """Convenience method for creating an aeolian ScaleType."""
        return cls.diatonic(5)

    @classmethod
    def natural_minor(cls) -> 'ScaleType':
        """Alias of :func:`ScaleType.aeolian`."""
        return cls.aeolian()

    @classmethod
    def locrian(cls) -> 'ScaleType':
        """Convenience method for creating an locrian ScaleType."""
        return cls.diatonic(6)

    @classmethod
    def harmonic_minor(cls, modal_shift: int = 0) -> 'ScaleType':
        """
        Returns a harmonic minor ScaleType with the specified modal shift.

        :param modal_shift: How many steps up or down to shift the starting note of the scale. The default value of
            zero creates the standard harmonic minor scale.
        """
        return cls(*ScaleType._standard_equal_tempered_patterns["harmonic minor"]).rotate(modal_shift)

    @classmethod
    def melodic_minor(cls, modal_shift: int = 0) -> 'ScaleType':
        """
        Returns a melodic minor ScaleType with the specified modal shift.

        :param modal_shift: How many steps up or down to shift the starting note of the scale. The default value of
            zero creates the standard melodic minor scale.
        """
        return cls(*ScaleType._standard_equal_tempered_patterns["melodic minor"]).rotate(modal_shift)

    @classmethod
    def whole_tone(cls) -> 'ScaleType':
        """Convenience method for creating a whole tone ScaleType."""
        return cls(*ScaleType._standard_equal_tempered_patterns["whole tone"])

    @classmethod
    def octatonic(cls, whole_step_first: bool = True) -> 'ScaleType':
        """
        Convenience method for creating an octatonic (alternating whole and half steps) ScaleType

        :param whole_step_first: whether to start with a whole step or a half step.
        """
        if whole_step_first:
            return cls(*ScaleType._standard_equal_tempered_patterns["octatonic"])
        else:
            return cls(*ScaleType._standard_equal_tempered_patterns["octatonic"]).rotate(1)

    # ------------------------------------- Loading / Saving ---------------------------------------

    def save_to_scala(self, file_path: str, description: str = "Mystery scale saved using SCAMP") -> None:
        """
        Converts and saves this ScaleType to a scala file at the given file path. Note that any intervals that combine
        cents and ratio information will be flattened out to only cents information, since the combination is not
        possible in scala files.

        :param file_path: path of the file to save
        :param description: description of the scale for the file header
        """
        lines = ["! {}".format(file_path.split("/")[-1]),
                 "!",
                 "{}".format(description),
                 str(len(self.intervals)),
                 "!"]
        lines.extend(interval.to_scala_string() for interval in self.intervals)
        with open(file_path, "w") as scala_file:
            scala_file.write("\n".join(lines))

    @classmethod
    def load_from_scala(cls, file_path: str) -> 'ScaleType':
        """
        Loads a ScaleType from a scala file.

        :param file_path: file path of a correctly formatted scala file
        """
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

    def _to_dict(self):
        return {
            "intervals": self.intervals
        }

    @classmethod
    def _from_dict(cls, json_dict):
        return cls(*json_dict["intervals"])

    def __repr__(self):
        return "ScaleType({})".format(self.intervals)


class Scale(SavesToJSON):

    """
    Class representing a scale starting on a specific pitch. A :class:`Scale` combines a :class:`ScaleType` with a
    starting pitch, and also an option as to whether the pitch collection should cycle (as pretty much all the
    standard scales do). To illustrate the difference between a :class:`ScaleType` and a :class:`Scale`, "D dorian"
    would be represented by a :class:`Scale`, whereas "dorian" would be represented by a :class:`ScaleType`.

    :param scale_type: a :class:`ScaleType` object
    :param start_pitch: a pitch to treat as the starting note of the scale
    :param cycle: whether or not this scale cycles. If so, the interval from the first pitch to the last pitch is
        treated as the cycle size.
    """

    def __init__(self, scale_type: ScaleType, start_pitch: Real, cycle: bool = True):
        self.scale_type = scale_type
        self._start_pitch = start_pitch
        self._cycle = cycle
        self._initialize_instance_vars()

    @property
    def start_pitch(self) -> Real:
        """The pitch that scale starts from."""
        return self._start_pitch

    @start_pitch.setter
    def start_pitch(self, value):
        self._start_pitch = value
        self._initialize_instance_vars()

    @property
    def cycle(self) -> bool:
        """Whether or not this scale repeats after a full cycle."""
        return self._cycle

    @cycle.setter
    def cycle(self, value):
        self._cycle = value
        self._initialize_instance_vars()

    def _initialize_instance_vars(self):
        # convert the scale type to a list of MIDI-valued seed pitches
        self._seed_pitches = (self._start_pitch,) + tuple(self._start_pitch + x for x in self.scale_type.to_half_steps())
        self._envelope = Envelope.from_points(*zip(range(len(self._seed_pitches)), self._seed_pitches))
        self._inverse_envelope = Envelope.from_points(*zip(self._seed_pitches, range(len(self._seed_pitches))))
        self.num_steps = len(self._seed_pitches) - 1
        self.width = self._seed_pitches[-1] - self._seed_pitches[0] if self._cycle else None

    @classmethod
    def from_pitches(cls, seed_pitches: Sequence[Real], cycle: bool = True) -> 'Scale':
        """
        Constructs a Scale from a list of seed pitches, given as floating-point MIDI pitch values. For instance, a
        C major scale could be constructed by calling Scale.from_pitches([60, 62, 64, 65, 67, 69, 71, 72]). Note that
        the upper C needs to be specified, since it is not assumed that scales will be octave repeating, and the repeat
        interval is given by the distance between the first and last seed pitch. Also note that this particular C major
        scale would place scale degree 0 at middle C, whereas Scale.from_pitches([48, 50, 52, 53, 55, 57, 59, 60]) would
        place it an octave lower.

        :param seed_pitches: a list of floating-point MIDI pitch values.
        :param cycle: Whether or not to cycle the scale, creating multiple "octaves" (or perhaps not octaves if the
            scale repeats at a different interval.
        """
        return cls(ScaleType(*(100. * (x - seed_pitches[0]) for x in seed_pitches[1:])), seed_pitches[0], cycle=cycle)

    @classmethod
    def from_scala_file(cls, file_path: str, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Constructs a Scale from a scala file located at the given file path, and a start pitch.

        :param file_path: path of the scala file to load
        :param start_pitch: the pitch to define as scale degree 0
        :param cycle: whether or not this scale is treated as cyclic
        """
        return cls(ScaleType.load_from_scala(file_path), start_pitch, cycle=cycle)

    @classmethod
    def from_start_pitch_and_cent_or_ratio_intervals(cls, start_pitch: Real, intervals, cycle: bool = True) -> 'Scale':
        """
        Creates a scale from a start pitch and a sequence of intervals (either cents or frequency ratios).

        :param start_pitch: The pitch to start on
        :param intervals: a sequence of intervals above the start pitch. These can be either :class:`PitchInterval`
            objects or anything that can be interpreted by :func:`PitchInterval.parse`.
        :param cycle: whether or not this scale is treated as cyclic. See explanation in :func:`Scale.from_pitches`
            about defining cyclic scales.
        """
        return cls(ScaleType(*intervals), start_pitch, cycle=cycle)

    def degree_to_pitch(self, degree: Real) -> float:
        """
        Given a degree of the scale, returns the pitch that it corresponds to. Degree 0 corresponds to the start
        pitch, and negative degrees correspond to notes below the start pitch (for cyclical scales). Fractional degrees
        are possible and result in pitches interpolated between the scale degrees
        
        :param degree: a (potentially floating-point) scale degree
        """
        if self._cycle:
            cycle_displacement = math.floor(degree / self.num_steps)
            mod_degree = degree % self.num_steps
            return self._envelope.value_at(mod_degree) + cycle_displacement * self.width
        else:
            return self._envelope.value_at(degree)

    def pitch_to_degree(self, pitch: Real) -> float:
        """
        Given a pitch, returns the scale degree that it corresponds to. Pitches that lie in between the notes of the
        scale will return fractional degrees via interpolation.

        :param pitch: a pitch, potentially in between scale degrees
        """
        if self._cycle:
            cycle_displacement = math.floor((pitch - self._seed_pitches[0]) / self.width)
            mod_pitch = (pitch - self._seed_pitches[0]) % self.width + self._seed_pitches[0]
            return self._inverse_envelope.value_at(mod_pitch) + cycle_displacement * self.num_steps
        else:
            return self._inverse_envelope.value_at(pitch)

    def round(self, pitch: Real) -> float:
        """Rounds the given pitch to the nearest note of the scale."""
        return self.degree_to_pitch(round(self.pitch_to_degree(pitch)))

    def floor(self, pitch: Real) -> float:
        """Returns the nearest note of the scale below or equal to the given pitch."""
        return self.degree_to_pitch(math.floor(self.pitch_to_degree(pitch)))

    def ceil(self, pitch: Real) -> float:
        """Returns the nearest note of the scale above or equal to the given pitch."""
        return self.degree_to_pitch(math.ceil(self.pitch_to_degree(pitch)))

    # ------------------------------------- Transformations ---------------------------------------

    def transpose(self, half_steps: float) -> 'Scale':
        """
        Transposes this scale (in place) by the given number of half steps.

        :param half_steps: number of half steps to transpose up or down by
        :return: self, for chaining purposes
        """
        self._start_pitch = self._start_pitch + half_steps
        self._initialize_instance_vars()
        return self
        
    def transposed(self, half_steps: float) -> 'Scale':
        """
        Same as :func:`Scale.transpose`, except that it returns a transposed copy, leaving this scale unaltered.
        """
        copy = self.duplicate()
        copy.transpose(half_steps)
        return copy

    # ------------------------------------- Class Methods ---------------------------------------

    @classmethod
    def chromatic(cls, start_pitch: Real = 60, cycle: bool = True) -> 'Scale':
        """
        Returns a 12-tone equal tempered chromatic scale starting on the specified pitch.

        :param start_pitch: the pitch this scale starts from (doesn't affect the scale in this case, but affects
            where we count scale degrees from).
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        """
        return cls(ScaleType.chromatic(), start_pitch, cycle=cycle)

    @classmethod
    def diatonic(cls, start_pitch: Real, modal_shift: int = 0, cycle: bool = True) -> 'Scale':
        """
        Returns a diatonic scale starting on the specified pitch, and with the specified modal shift.

        :param start_pitch: the pitch this scale starts from
        :param modal_shift: how many steps up or down to shift the scale's interval relationships. 0 is ionian, 1 is
            dorian, 2 is phrygian, etc. (There are also convenience methods for creating these modal scales.)
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        """
        return cls(ScaleType.diatonic(modal_shift), start_pitch, cycle=cycle)

    @classmethod
    def major(cls, start_pitch: Real, modal_shift: int = 0, cycle: bool = True) -> 'Scale':
        """Alias of :func:`Scale.diatonic`."""
        return cls.diatonic(start_pitch, modal_shift, cycle)

    @classmethod
    def ionian(cls, start_pitch: Real, modal_shift: int = 0, cycle: bool = True) -> 'Scale':
        """Alias of :func:`Scale.diatonic`."""
        return cls.diatonic(start_pitch, modal_shift, cycle)

    @classmethod
    def dorian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a dorian scale with the given start pitch. (Same as :func:`Scale.diatonic` with
        a modal shift of 1.)
        """
        return cls(ScaleType.dorian(), start_pitch, cycle=cycle)

    @classmethod
    def phrygian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a phrygian scale with the given start pitch. (Same as :func:`Scale.diatonic`
        with a modal shift of 2.)
        """
        return cls(ScaleType.phrygian(), start_pitch, cycle=cycle)

    @classmethod
    def lydian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a lydian scale with the given start pitch. (Same as :func:`Scale.diatonic`
        with a modal shift of 3.)
        """
        return cls(ScaleType.lydian(), start_pitch, cycle=cycle)

    @classmethod
    def mixolydian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a mixolydian scale with the given start pitch. (Same as :func:`Scale.diatonic`
        with a modal shift of 4.)
        """
        return cls(ScaleType. mixolydian(), start_pitch, cycle=cycle)

    @classmethod
    def aeolian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a aeolian scale with the given start pitch. (Same as :func:`Scale.diatonic`
        with a modal shift of 5.)
        """
        return cls(ScaleType.aeolian(), start_pitch, cycle=cycle)

    @classmethod
    def natural_minor(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """Alias of :func:`Scale.aeolian`."""
        return cls.aeolian(start_pitch, cycle)

    @classmethod
    def locrian(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Convenience method for creating a locrian scale with the given start pitch. (Same as :func:`Scale.diatonic`
        with a modal shift of 6.)
        """
        return cls(ScaleType.locrian(), start_pitch, cycle=cycle)

    @classmethod
    def harmonic_minor(cls, start_pitch: Real, modal_shift: int = 0, cycle: bool = True) -> 'Scale':
        """
        Returns a harmonic minor scale starting on the specified pitch, and with the specified modal shift.

        :param start_pitch: the pitch this scale starts from
        :param modal_shift: How many steps up or down to shift the scale's interval relationships. To get a regular
            harmonic minor scale, simply use the default modal shift of 0.
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        """
        return cls(ScaleType.harmonic_minor(modal_shift), start_pitch, cycle=cycle)

    @classmethod
    def melodic_minor(cls, start_pitch: Real, modal_shift: int = 0, cycle: bool = True) -> 'Scale':
        """
        Returns a melodic minor scale starting on the specified pitch, and with the specified modal shift.

        :param start_pitch: the pitch this scale starts from
        :param modal_shift: How many steps up or down to shift the scale's interval relationships. To get a regular
            melodic minor scale, simply use the default modal shift of 0. A so-called acoustic scale (major sharp-4,
            flat-7) can be produced with a modal shift of 4.
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        """
        return cls(ScaleType.melodic_minor(modal_shift), start_pitch, cycle=cycle)

    @classmethod
    def whole_tone(cls, start_pitch: Real, cycle: bool = True) -> 'Scale':
        """
        Returns a whole tone scale with the given start pitch.

        :param start_pitch: the pitch this scale starts from
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        """
        return cls(ScaleType.whole_tone(), start_pitch, cycle=cycle)

    @classmethod
    def octatonic(cls, start_pitch: Real, cycle: bool = True, whole_step_first: bool = True) -> 'Scale':
        """
        Returns an octatonic scale with the given start pitch.

        :param start_pitch: the pitch this scale starts from
        :param cycle: whether or not this scale repeats after an octave or is constrained to a single octave.
        :param whole_step_first: whether this is a whole-half or half-whole octatonic scale.
        """
        return cls(ScaleType.octatonic(whole_step_first=whole_step_first), start_pitch, cycle=cycle)

    # ------------------------------------- Loading / Saving ---------------------------------------

    def _to_dict(self):
        return {
            "scale_type": self.scale_type,
            "start_pitch": self._start_pitch,
            "cycle": self._cycle
        }

    @classmethod
    def _from_dict(cls, json_dict):
        return cls(**json_dict)

    # ------------------------------------- Special Methods ---------------------------------------

    def __iter__(self):
        for step_num in range(self.num_steps + 1):
            yield self.degree_to_pitch(step_num)

    def __repr__(self):
        return "Scale({}, {}{})".format(
            repr(self.scale_type),
            self._start_pitch,
            ", cycle={}".format(self._cycle) if not self._cycle else ""
        )
