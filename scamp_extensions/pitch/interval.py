from fractions import Fraction
from scamp.utilities import SavesToJSON
from ..utils import ratio_to_cents


class PitchInterval(SavesToJSON):

    def __init__(self, cents: float, ratio: Fraction):
        """
        Represents an interval between two pitches.

        :param cents: cents displacement
        :param ratio: frequency ratio, either instead of or in addition to the cents displacement
        """

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
            return cls. _from_json(representation)
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

    def to_cents(self):
        return self.cents + ratio_to_cents(self.ratio)

    def to_half_steps(self):
        return self.to_cents() / 100

    def to_scala_string(self):
        if self.cents == 0 and self.ratio == 1:
            return "0."
        elif self.cents == 0:
            return str(self.ratio)
        elif self.ratio == 1:
            return str(self.cents)
        else:
            return str(self.to_cents())

    # ------------------------------------- Loading / Saving ---------------------------------------

    def _to_json(self):
        return {"cents": self.cents, "ratio": [self.ratio.numerator, self.ratio.denominator]}

    @classmethod
    def _from_json(cls, json_object):
        json_object["ratio"] = Fraction(*json_object["ratio"])
        return cls(**json_object)

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