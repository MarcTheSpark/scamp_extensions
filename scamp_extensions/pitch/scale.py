from expenvelope import Envelope
import math


class Scale:

    def __init__(self, seed_pitches, cyclic=False):
        if not (len(seed_pitches) > 1 and all(a < b for a, b in zip(seed_pitches[:-1], seed_pitches[1:]))):
            raise ValueError("Scale seed must be a list of two or more pitches in ascending order")
        self._envelope = Envelope.from_points(*zip(range(len(seed_pitches)), seed_pitches))
        self._inverse_envelope = Envelope.from_points(*zip(seed_pitches, range(len(seed_pitches))))
        self._cycle_length = len(seed_pitches) - 1 if cyclic else None
        self._cycle_interval = seed_pitches[-1] - seed_pitches[0] if cyclic else None
        self._seed_pitches = seed_pitches

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
