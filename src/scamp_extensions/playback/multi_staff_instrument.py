"""
This module defines the :class:`~scamp_extensions.playback.multi_staff_instrument.MultiStaffInstrument` class,
a convenience class that combines multiple :class:`ScampInstrument` objects so that they can create a single part in
the score. A typical use case would be to combine arco, pizzicato and harmonic presets from a soundfont into a single
string instrument part.
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

from __future__ import annotations
from clockblocks import Clock
from scamp import ScampInstrument, SpellingPolicy, Envelope
from scamp.utilities import NoteProperty
from typing import Callable, Sequence


class MultiStaffInstrument:
    """
    A convenient wrapper for bundling multiple `ScampInstrument` objects into a single meta instrument that
    represents a grand staff of group of staves.

    :param name: name of this instrument
    :param staff_parts: list of ScampInstrument objects that represent the different staves
    :param decision_protocol: either a tuple of pitch boundaries that decide which part plays
        or a function that maps pitch to part index.
    """

    def __init__(self, name: str, staff_parts: Sequence[ScampInstrument],
                 decision_protocol: Callable[[float], int] | Sequence = (60,)):
        self.name = name
        self.staff_parts = staff_parts
        if isinstance(decision_protocol, Callable):
            self.decision_function = decision_protocol
        else:
            assert len(decision_protocol) + 1 == len(staff_parts), \
                f"Wrong number of decision boundaries for {len(staff_parts)} instruments"

            def decision_function(p):
                i = 0
                for pitch_boundary in decision_protocol:
                    if p >= pitch_boundary:
                        i += 1
                    else:
                        break
                return len(decision_protocol) - i

            self.decision_function = decision_function

    @staticmethod
    def _pitch_value_to_float(pitch):
        if isinstance(pitch, Envelope):
            return pitch.start_level()
        elif hasattr(pitch, '__len__'):
            return Envelope.from_list(pitch).start_level()
        else:
            return pitch

    def play_note(self, pitch, volume, length, properties: Union[str, dict, Sequence, NoteProperty] = None,
                  force_staff: int = None, blocking: bool = True, clock: Clock = None) -> None:
        """
        Play a note using this MultiStaffInstrument

        :param pitch: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param length: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param force_staff: force this note to play on the given staff index
        :param properties: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param blocking: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param clock: see :func:`~scamp.instruments.ScampInstrument.play_note`
        """

        if pitch is None:
            # so that we don't call the decision function on a rest
            staff_index = 0
        elif force_staff:
            staff_index = force_staff
        else:
            staff_index = self.decision_function(MultiStaffInstrument._pitch_value_to_float(pitch))

        self.staff_parts[staff_index].play_note(
            pitch, volume, length, properties=properties, blocking=blocking, clock=clock
        )

    def play_chord(self, pitches: Sequence, volume, length, properties: Union[str, dict, Sequence, NoteProperty] = None,
                   force_staff: int = None, blocking: bool = True, clock: Clock = None) -> None:
        """
        Play a chord using this MultiPresetInstrument.

        :param pitches: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param length: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param force_staff: force this chord to play on the given staff index
        :param blocking: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param clock: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        """
        if pitches is None:
            # so that we don't call the decision function on a rest
            staff_index = 0
        elif force_staff:
            staff_index = force_staff
        else:
            average_pitch = sum(
                MultiStaffInstrument._pitch_value_to_float(pitch)
                for pitch in pitches
            ) / len(pitches)
            staff_index = self.decision_function(average_pitch)

        self.staff_parts[staff_index].play_chord(
            pitches, volume, length, properties=properties, blocking=blocking, clock=clock
        )

    def start_note(self, pitch: float, volume: float, properties: Union[str, dict, Sequence, NoteProperty] = None,
                   force_staff: int = None, clock: Clock = None, fixed: Union[bool, str] = "auto",
                   velocity: float = None) -> MultiNoteHandle:
        """
        Start a note using this MultiPresetInstrument.

        :param pitch: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param force_staff: force this note to play on the given staff index
        :param clock: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param fixed: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param velocity: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :return: a :class:`MultiNoteHandle` with which to later manipulate the note
        """

        if pitch is None:
            # so that we don't call the decision function on a rest
            staff_index = 0
        elif force_staff:
            staff_index = force_staff
        else:
            staff_index = self.decision_function(MultiStaffInstrument._pitch_value_to_float(pitch))

        return self.staff_parts[staff_index].start_note(
            pitch, volume, properties,
            clock=clock, fixed=fixed, velocity=velocity
        )

    def start_chord(self, pitches: Sequence[float], volume: float,
                    properties: Union[str, dict, Sequence, NoteProperty] = None, force_staff: int = None,
                    clock: Clock = None, fixed: Union[bool, str] = "auto", velocity: float = None) -> MultiNoteHandle:
        """
        Start a note using this MultiPresetInstrument.

        :param pitches: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param force_staff: force this chord to play on the given staff index
        :param clock: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param fixed: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param velocity: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :return: a :class:`MultiNoteHandle` with which to later manipulate the chord
        """
        if pitches is None:
            # so that we don't call the decision function on a rest
            staff_index = 0
        elif force_staff:
            staff_index = force_staff
        else:
            average_pitch = sum(
                MultiStaffInstrument._pitch_value_to_float(pitch)
                for pitch in pitches
            ) / len(pitches)
            staff_index = self.decision_function(average_pitch)

        return self.staff_parts[staff_index].start_chord(
            pitches, volume, properties,
            clock=clock, fixed=fixed, velocity=velocity
        )

    def send_midi_cc(self, cc_number: int, value_from_0_to_1: float) -> None:
        """
        Send a midi cc message to every :class:`~scamp.instruments.ScampInstrument:` used by this MultiPresetInstrument.

        :param cc_number: MIDI cc number
        :param value_from_0_to_1: value to send (scaled from 0 to 1)
        """
        for instrument in self.staff_parts:
            instrument.send_midi_cc(cc_number, value_from_0_to_1)

    def end_all_notes(self) -> None:
        """
        Ends all notes currently playing
        """
        for instrument in self.staff_parts:
            instrument.end_all_notes()

    def num_notes_playing(self) -> int:
        """
        Returns the number of notes currently playing.
        """
        return sum(instrument.num_notes_playing() for instrument in self.staff_parts)

    def set_max_pitch_bend(self, semitones: int) -> None:
        """
        Set the max pitch bend for all midi playback implementations on this instrument
        """
        for instrument in self.staff_parts:
            instrument.set_max_pitch_bend(semitones)

    @property
    def default_spelling_policy(self):
        """
        The default spelling policy for notes played back by this instrument.
        See :class:`~scamp.instruments.ScampInstrument`
        """
        return self.staff_parts[0].default_spelling_policy

    @default_spelling_policy.setter
    def default_spelling_policy(self, value: Union[SpellingPolicy, str]):
        for instrument in self.staff_parts:
            instrument.default_spelling_policy = value


