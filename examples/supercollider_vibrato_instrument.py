
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

from scamp import *
from scamp_extensions.supercollider import add_sc_extensions
import random

add_sc_extensions()

s = Session()

engraving_settings.show_microtonal_annotations = False
engraving_settings.glissandi.include_end_grace_note = False


vib = s.new_supercollider_part("vibrato", r"""
    SynthDef(\vibSynth, { |out=0, freq=440, volume=0.1, vibFreq=20, vibWidth=0.5, gate=1|
        var envelope = EnvGen.ar(Env.asr(releaseTime:0.5), gate, doneAction: 2);
        var vibHalfSteps = SinOsc.ar(vibFreq) * vibWidth;
        var vibFreqMul = 2.pow(vibHalfSteps / 12);
        var vibSine =  SinOsc.ar(freq * vibFreqMul) * volume / 10;
        Out.ar(out, (envelope * vibSine) ! 2);
    }, [\ir, 0.1, 0.1, 0.1, 0.1, \kr])
""")

s.start_transcribing()
# This line actually tells SuperCollider to do an audio recording
s.start_recording_sc_output("vibby.wav")


s.set_tempo_target(300, 15, duration_units="time")

while s.time() < 15:
    vib.play_note([random.uniform(62, 90), random.uniform(62, 90)], [0, 1, 0], (1.75, 0.25),
        {"vibWidth_param": [0, 3.5],
         "vibFreq_param": [30, 0]}
    )

s.stop_transcribing().to_score("4/4").show_xml()
s.stop_recording_sc_output()
