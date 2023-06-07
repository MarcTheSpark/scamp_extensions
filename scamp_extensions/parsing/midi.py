"""
Utilities for scraping notes from MIDI files.
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

from typing import List
from mido import MidiFile
from collections import namedtuple

Note = namedtuple("Note", "track channel pitch volume start_time length")


def scrape_midi_file_to_note_list(midi_file_path) -> List[Note]:
    """
    Scrapes a list of :class:`Note` objects from all of the tracks of the given MIDI file.

    :param midi_file_path: path to midi file
    """
    mid = MidiFile(midi_file_path, clip=True)

    notes_started = {}
    notes = []

    for which_track, track in enumerate(mid.tracks):
        t = 0
        for message in track:
            t += message.time / mid.ticks_per_beat
            if message.type == "note_off" or (message.type == "note_on" and message.velocity == 0):
                try:
                    volume, start_time = notes_started[(message.note, message.channel)]
                    notes.append(Note(which_track, message.channel, message.note, volume, start_time, t - start_time))
                except KeyError:
                    print("KEY ERROR")
                    pass
            elif message.type == "note_on":
                notes_started[(message.note, message.channel)] = message.velocity / 127, t

    notes.sort(key=lambda note: note.start_time)
    return notes


def scrape_midi_file_to_dict(midi_file_path) -> dict:
    """
    Scrapes a dictionary of note info from a MIDI file.

    :param midi_file_path: the MIDI file path
    :return: a dict with the following keys, each of which is presented in chronological order of the notes from which
        they derive: "pitches", "start_times", "volumes", "lengths", "inter_onset_times" (how long since the last note
        started), "tracks"
    """
    notes = scrape_midi_file_to_note_list(midi_file_path)

    tracks, channels, pitches, volumes, start_times, lengths = zip(*notes)
    tracks = list(tracks)
    pitches = list(pitches)
    start_times = list(start_times)
    volumes = list(volumes)
    lengths = list(lengths)
    inter_onset_times = [t2 - t1 for t1, t2 in zip(start_times[:-1], start_times[1:])]

    return {
        "pitches": pitches,
        "start_times": start_times,
        "volumes": volumes,
        "lengths": lengths,
        "inter_onset_times": inter_onset_times,
        "tracks": tracks
    }
