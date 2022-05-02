"""
This module defines the :class:`~scamp_extensions.utilities.time_varying_parameter.TimeVaryingParameter` class,
a convenience subclasses of :class:`~expenvelope.envelope.Envelope` that is aware of the clock and can be called
to look up its value at the current beat or time.
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
from typing import Sequence, Union, Callable
from clockblocks import current_clock, Clock
from expenvelope import Envelope, EnvelopeSegment
from expenvelope.envelope import T


class TimeVaryingParameter(Envelope):

    """
    A simple wrapper around :class:`~expenvelope.envelope.Envelope` that is aware of the current time or beat in the
    current clock. Simply call it like a function to get its value at the current time or beat.

    :param levels: see :class:`~expenvelope.envelope.Envelope`
    :param durations: see :class:`~expenvelope.envelope.Envelope`
    :param curve_shapes: see :class:`~expenvelope.envelope.Envelope`
    :param offset: see :class:`~expenvelope.envelope.Envelope`
    :param clock: the clock whose time/beat this TimeVaryingParameter uses for lookup. Defaults to the current active clock.
    :param units: either "beats" or "time"; whether or not to use the time or the beat of the clock to look up the
        parameter value
    """

    def __init__(self, levels: Sequence = (0,), durations: Sequence[float] = (),
                 curve_shapes: Sequence[Union[float, str]] = None, offset: float = 0,
                 clock: Clock = None, units: str = "beats"):

        super().__init__(levels=levels, durations=durations, curve_shapes=curve_shapes, offset=offset)
        self._initialize(clock, units)

    def _initialize(self, clock, units):
        if units not in ("beats", "time"):
            raise ValueError("`units` argument must be either \"beats\" or \"time\"")
        self.clock = current_clock() if clock is None else clock
        if self.clock is None:
            raise ValueError("No clock was specified, and there was no clock available on the current thread. (Did"
                             "you create this TimeVaryingParameter before creating a Session or master clock?)")
        self.get_moment = self.clock.time if units == "time" else self.clock.beat
        self.instantiation_time = self.get_moment()

    def finished(self):
        return self.get_moment() - self.instantiation_time >= self.length()

    @classmethod
    def from_segments(cls, segments: Sequence[EnvelopeSegment], clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_segments`, but taking an optional clock and units parameter.
        (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_segments(segments)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def from_levels_and_durations(cls, levels: Sequence, durations: Sequence[float],
                                  curve_shapes: Sequence[Union[float, str]] = None, offset: float = 0,
                                  clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_levels_and_durations`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_levels_and_durations(levels, durations, curve_shapes, offset)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def from_levels(cls, levels: Sequence, length: float = 1.0, offset: float = 0,
                    clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_levels`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_levels(levels, length, offset)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def from_list(cls, constructor_list: Sequence, clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_list`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_list(constructor_list)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def from_points(cls, *points: Sequence, clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_points`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_points(*points)
        instance._initialize(clock, units)
        return instance
    @classmethod
    def release(cls, duration: float, start_level=1, curve_shape: Union[float, str] = None,
                clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.release`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().release(duration, start_level, curve_shape)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def ar(cls, attack_length: float, release_length: float, peak_level=1,
           attack_shape: Union[float, str] = None, release_shape: Union[float, str] = None,
           clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.ar`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().ar(attack_length, release_length, peak_level, attack_shape, release_shape)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def asr(cls, attack_length: float, sustain_level, sustain_length: float, release_length: float,
            attack_shape: Union[float, str] = None, release_shape: Union[float, str] = None,
            clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.asr`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().asr(attack_length, sustain_level, sustain_length,
                               release_length, attack_shape, release_shape)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def adsr(cls, attack_length: float, attack_level, decay_length: float, sustain_level, sustain_length: float,
             release_length: float, attack_shape: Union[float, str] = None, decay_shape: Union[float, str] = None,
             release_shape: Union[float, str] = None, clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.adsr`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().adsr(attack_length, attack_level, decay_length, sustain_level, sustain_length,
                                release_length, attack_shape, decay_shape, release_shape)
        instance._initialize(clock, units)
        return instance

    @classmethod
    def from_function(cls, function: Callable[[float], float], domain_start: float = 0, domain_end: float = 1,
                      resolution_multiple: int = 2, key_point_precision: int = 2000,
                      key_point_iterations: int = 5, clock: Clock = None, units: str = "beats") -> T:
        """
        Same as :func:`~expenvelope.envelope.Envelope.from_function`, but taking an optional clock and units
        parameter. (See :class:`TimeVaryingParameter`)
        """
        instance = super().from_function(function, domain_start, domain_end, resolution_multiple,
                                         key_point_precision, key_point_iterations)
        instance._initialize(clock, units)
        return instance

    def __call__(self, *args, **kwargs):
        return self.value_at(self.get_moment() - self.instantiation_time)
