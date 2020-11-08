"""
This module defines the :class:`~scamp_extensions.playback.multi_preset_instrument.MultiPresetInstrument` class,
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

import logging
from clockblocks import Clock
from scamp import ScampInstrument, Session, SpellingPolicy, NoteProperties, NoteHandle, ChordHandle
from scamp.utilities import NoteProperty
from typing import Sequence, Optional, Union, Tuple


class MultiPresetInstrument:
    """
    A convenient wrapper for bundling multiple `ScampInstrument` objects or soundfont presets into a single notated
    part, and assigning particular notations to these presets.

    :param session: the session in which this MultiPresetInstrument operates
    :param name: name of this MultiPresetInstrument (e.g. in the score)
    :param default_spelling_policy: see :class:`~scamp.instruments.ScampInstrument`
    :param clef_preference: see :class:`~scamp.instruments.ScampInstrument`
    """

    def __init__(self, session: Session, name: str, default_spelling_policy: Optional[SpellingPolicy] = None,
                 clef_preference: str = "from_name"):
        self.host_session = session
        self.notation_part = self.host_session.new_silent_part(name, default_spelling_policy, clef_preference)
        self.presets = []
        self.last_preset_played = None

    @property
    def name(self):
        """Name of this MultiPresetInstrument (e.g. in the score)"""
        return self.notation_part.name

    @name.setter
    def name(self, value):
        self.notation_part.name = value

    def add_preset(self, name: str, instrument_or_soundfont_preset: Union[ScampInstrument, str, int, Tuple[int, int]],
                   bundled_properties: Union[str, dict, Sequence, NoteProperty] = None,
                   bundled_properties_on_switch: Union[str, dict, Sequence, NoteProperty] = None,
                   bundled_properties_on_switch_away: Union[str, dict, Sequence, NoteProperty] = None,
                   make_default=False):
        """
        Add a new preset with a given instrument and name.

        :param instrument_or_soundfont_preset: either a ScampInstrument, or a soundfont preset name or number.
        :param name: name for this preset used when calling play_note
        :param bundled_properties: Any properties that we wish to bundle with every note played by this preset. For
            example, diamond noteheads for harmonics.
        :param bundled_properties_on_switch: Any properties that we wish to bundle with this preset when we switch to
            it (the last note was a different preset). For example, "pizz."
        :param bundled_properties_on_switch_away: Any properties that we wish to bundle with this preset when we switch
            to it (the last note was a different preset). For example, "pizz."
        :param make_default: if True, moves this preset to the front of the list so that it becomes the default
            preset. If this is the first preset defined, it will become the default regardless of the setting of
            this parameter.
        :return: self, for chaining purposes
        """
        if bundled_properties is not None:
            bundled_properties = NoteProperties.from_unknown_format(bundled_properties)
        if bundled_properties_on_switch is not None:
            bundled_properties_on_switch = NoteProperties.from_unknown_format(bundled_properties_on_switch)
        if bundled_properties_on_switch_away is not None:
            bundled_properties_on_switch_away = NoteProperties.from_unknown_format(bundled_properties_on_switch_away)

        inst = instrument_or_soundfont_preset if isinstance(instrument_or_soundfont_preset, ScampInstrument) else \
            self.host_session.new_part("{}-{}".format(self.notation_part.name, name), instrument_or_soundfont_preset)
        preset = (name, inst, bundled_properties, bundled_properties_on_switch, bundled_properties_on_switch_away)
        if make_default:
            self.presets.insert(0, preset)
        else:
            self.presets.append(preset)
        return self

    def _get_preset_index(self, preset_name: str) -> Union[int, None]:
        names = [x[0] for x in self.presets]
        if preset_name in names:
            return [x[0] for x in self.presets].index(preset_name)
        else:
            return None

    def _resolve_preset(self, preset_name: str) -> Tuple[str, ScampInstrument, NoteProperties,
                                                         NoteProperties, NoteProperties]:
        if len(self.presets) == 0:
            return None, None, None, None, None
        elif preset_name is None:  # use the default preset
            return self.presets[0]
        else:
            index = self._get_preset_index(preset_name)
            if index is None:
                logging.warning("MultiPresetInstrument {} could not resolve preset {}. Falling back to default preset".
                                format(self.name, preset_name))
                return self.presets[0]
            return self.presets[index]

    def _check_if_switched(self, preset_name) -> bool:
        if self.last_preset_played is None:
            # if no note has been played, we count it as a switch if a non-default preset is used
            switched = preset_name != self.presets[0][0]
        else:
            switched = self.last_preset_played != preset_name
        return switched

    def _resolve_properties(self, preset_name, note_properties, preset_properties, preset_switch_properties):
        # make preset_switch_properties None unless it switched. _check_if_switched also keeps track of last preset
        if self._check_if_switched(preset_name):
            preset_switch_properties = preset_switch_properties if self._check_if_switched(preset_name) else None
            last_preset_switch_away_properties = self._resolve_preset(self.last_preset_played)[4] \
                if self.last_preset_played is not None else None
        else:
            last_preset_switch_away_properties = None

        self.last_preset_played = preset_name
        # make a blank of NoteProperties and incorporate all of the preset properties
        return NoteProperties().incorporate(preset_properties).\
            incorporate(last_preset_switch_away_properties).\
            incorporate(preset_switch_properties).\
            incorporate(NoteProperties.from_unknown_format(note_properties))

    def play_note(self, pitch, volume, length, properties: Union[str, dict, Sequence, NoteProperty] = None,
                  preset: str = None, blocking: bool = True, clock: Clock = None) -> None:
        """
        Play a note using this MultiPresetInstrument

        :param pitch: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param length: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param preset: Name of the preset to use for this note.
        :param properties: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param blocking: see :func:`~scamp.instruments.ScampInstrument.play_note`
        :param clock: see :func:`~scamp.instruments.ScampInstrument.play_note`
        """
        preset, preset_inst, preset_properties, preset_switch_properties, _ = self._resolve_preset(preset)

        if preset_inst is not None:
            # this will happen so long as there's a preset to resolve to
            properties = self._resolve_properties(preset, properties, preset_properties, preset_switch_properties)
            preset_inst.play_note(pitch, volume, length, properties=properties, blocking=False, clock=clock,
                                  transcribe=False)
        else:
            logging.warning("MultiPresetInstrument {} does not have any presets. (Probably a mistake?)".
                            format(self.name))

        self.notation_part.play_note(pitch, volume, length, properties=properties, blocking=blocking, clock=clock)

    def play_chord(self, pitches: Sequence, volume, length, properties: Union[str, dict, Sequence, NoteProperty] = None,
                   preset: str = None, blocking: bool = True, clock: Clock = None) -> None:
        """
        Play a chord using this MultiPresetInstrument.

        :param pitches: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param length: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param preset: Name of the preset to use for this chord.
        :param blocking: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        :param clock: see :func:`~scamp.instruments.ScampInstrument.play_chord`
        """
        preset, preset_inst, preset_properties, preset_switch_properties, _ = self._resolve_preset(preset)

        if preset_inst is not None:
            # this will happen so long as there's a preset to resolve to
            properties = self._resolve_properties(preset, properties, preset_properties, preset_switch_properties)
            preset_inst.play_chord(pitches, volume, length, properties=properties, blocking=False, clock=clock,
                                   transcribe=False)
        else:
            logging.warning("MultiPresetInstrument {} does not have any presets. (Probably a mistake?)".
                            format(self.name))

        self.notation_part.play_chord(pitches, volume, length, properties=properties, blocking=blocking, clock=clock)

    def start_note(self, pitch: float, volume: float, properties: Union[str, dict, Sequence, NoteProperty] = None,
                   preset: str = None, clock: Clock = None, max_volume: float = 1) -> 'MultiNoteHandle':
        """
        Start a note using this MultiPresetInstrument.

        :param pitch: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param preset: name of the preset to use for this note.
        :param clock: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :param max_volume: see :func:`~scamp.instruments.ScampInstrument.start_note`
        :return: a :class:`MultiNoteHandle` with which to later manipulate the note
        """
        preset, preset_inst, preset_properties, preset_switch_properties, _ = self._resolve_preset(preset)

        handles = []
        if preset_inst is not None:
            # this will happen so long as there's a preset to resolve to
            properties = self._resolve_properties(preset, properties, preset_properties, preset_switch_properties)
            handles.append(preset_inst.start_note(pitch, volume, properties,
                                                  clock=clock, max_volume=max_volume, flags="no_transcribe"))
        else:
            logging.warning("MultiPresetInstrument {} does not have any presets. (Probably a mistake?)".
                            format(self.name))
        handles.append(self.notation_part.start_note(pitch, volume, properties, clock=clock, max_volume=max_volume))
        return MultiNoteHandle(handles)

    def start_chord(self, pitches: Sequence[float], volume: float,
                    properties: Union[str, dict, Sequence, NoteProperty] = None, preset: str = None,
                    clock: Clock = None, max_volume: float = 1) -> 'MultiNoteHandle':
        """
        Start a note using this MultiPresetInstrument.

        :param pitches: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param volume: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param properties: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param preset: name of the preset to use for this note.
        :param clock: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :param max_volume: see :func:`~scamp.instruments.ScampInstrument.start_chord`
        :return: a :class:`MultiNoteHandle` with which to later manipulate the chord
        """
        preset, preset_inst, preset_properties, preset_switch_properties, _ = self._resolve_preset(preset)

        handles = []
        if preset_inst is not None:
            # this will happen so long as there's a preset to resolve to
            properties = self._resolve_properties(preset, properties, preset_properties, preset_switch_properties)
            handles.append(preset_inst.start_chord(pitches, volume, properties,
                                                   clock=clock, max_volume=max_volume, flags="no_transcribe"))
        else:
            logging.warning("MultiPresetInstrument {} does not have any presets. (Probably a mistake?)".
                            format(self.name))
        handles.append(self.notation_part.start_chord(pitches, volume, properties, clock=clock, max_volume=max_volume))
        return MultiNoteHandle(handles)

    def send_midi_cc(self, cc_number: int, value_from_0_to_1: float) -> None:
        """
        Send a midi cc message to every :class:`~scamp.instruments.ScampInstrument:` used by this MultiPresetInstrument.

        :param cc_number: MIDI cc number
        :param value_from_0_to_1: value to send (scaled from 0 to 1)
        """
        for _, preset_inst, _, _ in self.presets:
            preset_inst.send_midi_cc(cc_number, value_from_0_to_1)

    def end_all_notes(self) -> None:
        """
        Ends all notes currently playing
        """
        for _, preset_inst, _, _ in self.presets:
            preset_inst.end_all_notes()

    def num_notes_playing(self) -> int:
        """
        Returns the number of notes currently playing.
        """
        return self.notation_part.num_notes_playing()

    def set_max_pitch_bend(self, semitones: int) -> None:
        """
        Set the max pitch bend for all midi playback implementations on this instrument
        """
        for _, preset_inst, _, _ in self.presets:
            preset_inst.set_max_pitch_bend(semitones)

    @property
    def clef_preference(self):
        """
        The clef preference for this instrument. See :class:`~scamp.instruments.ScampInstrument`
        """
        return self.notation_part.clef_preference

    @clef_preference.setter
    def clef_preference(self, value):
        self.notation_part.clef_preference = value

    @property
    def default_spelling_policy(self):
        """
        The default spelling policy for notes played back by this instrument.
        See :class:`~scamp.instruments.ScampInstrument`
        """
        return self.notation_part.default_spelling_policy

    @default_spelling_policy.setter
    def default_spelling_policy(self, value: Union[SpellingPolicy, str]):
        self.notation_part.default_spelling_policy = value


class MultiNoteHandle:
    """
    The equivalent of an :class:`~scamp.instruments.NoteHandle` but for a :class:`MultiPresetInstrument`.

    :param note_handles: a list of the NoteHandles for the underlying ScampInstruments. (One for the silent
        notation part, and one for the active preset.)
    """

    def __init__(self, note_handles: Sequence[Union[NoteHandle, ChordHandle]] = ()):
        self.note_handles = note_handles

    def change_parameter(self, param_name: str, target_value_or_values: Union[float, Sequence],
                         transition_length_or_lengths: Union[float, Sequence] = 0,
                         transition_curve_shape_or_shapes: Union[float, Sequence] = 0, clock: Clock = None) -> None:
        """
        See :func:`~scamp.instruments.NoteHandle.change_parameter`
        """
        for note_handle in self.note_handles:
            note_handle.change_parameter(param_name, target_value_or_values, transition_length_or_lengths,
                                         transition_curve_shape_or_shapes, clock)

    def change_pitch(self, target_value_or_values: Union[float, Sequence],
                     transition_length_or_lengths: Union[float, Sequence] = 0,
                     transition_curve_shape_or_shapes: Union[float, Sequence] = 0, clock: Clock = None) -> None:
        """
        See :func:`~scamp.instruments.NoteHandle.change_pitch`
        """
        for note_handle in self.note_handles:
            note_handle.change_pitch(target_value_or_values, transition_length_or_lengths,
                                     transition_curve_shape_or_shapes, clock)

    def change_volume(self,  target_value_or_values: Union[float, Sequence],
                      transition_length_or_lengths: Union[float, Sequence] = 0,
                      transition_curve_shape_or_shapes: Union[float, Sequence] = 0, clock: Clock = None) -> None:
        """
        See :func:`~scamp.instruments.NoteHandle.change_volume`
        """
        for note_handle in self.note_handles:
            note_handle.change_volume(target_value_or_values, transition_length_or_lengths,
                                      transition_curve_shape_or_shapes, clock)

    def split(self) -> None:
        """
        See :func:`~scamp.instruments.NoteHandle.split`
        """
        for note_handle in self.note_handles:
            note_handle.split()

    def end(self) -> None:
        """
        See :func:`~scamp.instruments.NoteHandle.end`
        """
        for note_handle in self.note_handles:
            note_handle.end()

    def __repr__(self):
        return "MultiNoteHandle({})".format(self.note_handles)
