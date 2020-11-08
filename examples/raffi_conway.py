"""
Example written by Raphael Radna
Adapted for SuperCollider by Marc Evanstein
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

import numpy
import matplotlib.pyplot as pyplot
import matplotlib.animation as animation
from scamp import *
from scamp_extensions.playback.supercollider import add_sc_extensions
import math

add_sc_extensions()


WIDTH = 24
HEIGHT = 24
s = Session()
scamp1 = s.new_supercollider_part("scamp1", r"""
    SynthDef(\sine, { |freq=440, volume=0, gate=1, pan=0|
        var sine = SinOsc.ar(freq, mul: volume.linexp(0, 1, 0.01, 1));
        var envelope = EnvGen.kr(Env.asr(attackTime:0.05, releaseTime:0.1), gate, doneAction:2);
        Out.ar(0, Pan2.ar(sine * envelope * volume, pan*2-1));
    }).add;
""")


def bark_to_hz(bark):  # Traunmüller formula
    return 1960 / (26.81 / (bark + 0.53) - 1)


def ftom(hz, base=440):
    return 12 * math.log(hz/base)/math.log(2) + 69


def init_grid(x, y):
    return numpy.random.choice([0, 1], (x, y))


def wrap(val, lo, hi):
    if val < lo:
        val += hi
    if val >= hi:
        val -= hi
    return val


def get_cell(a, x, y, dx, dy):
    return a[wrap((x + dx), 0, WIDTH), wrap((y + dy), 0, HEIGHT)]


def sum_neighbors(a, x, y):
    running_sum = 0
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            running_sum += get_cell(a, x, y, i - 1, j - 1)
    return running_sum


def apply_rules(a, b, x, y):
    state = a[x, y]
    neighbor_count = sum_neighbors(a, x, y)
    if state == 1 and (neighbor_count < 2 or neighbor_count > 3):
        b[x, y] = 0
    if state == 0 and neighbor_count == 3:
        b[x, y] = 1


current_grid = init_grid(WIDTH, HEIGHT)
next_grid = numpy.array(current_grid)
note_grid = numpy.zeros((WIDTH, HEIGHT), dtype=object)


def grid_play(a, x, y):
    pan = y / HEIGHT
    # pitch = 72 * (x / WIDTH) + 24 + pan
    pitch = ftom(bark_to_hz((x / WIDTH) * 24 + pan))
    cell_state = a[x, y]
    note_state = note_grid[x, y]

    if cell_state == 1 and note_state == 0:
        note_grid[x, y] = scamp1.start_note(pitch, 0.125, "pan_param:{}".format(pan))

    if cell_state == 0 and note_state != 0:
        note_grid[x, y].end()
        note_grid[x, y] = 0


def update_grid(*args):
    global current_grid
    global next_grid
    for x in range(WIDTH):
        for y in range(HEIGHT):
            grid_play(current_grid, x, y)
            apply_rules(current_grid, next_grid, x, y)
    current_grid[:, :] = next_grid[:, :]
    im.set_array(next_grid)
    return im,


fig, ax = pyplot.subplots(figsize=(4, 4))
ax.set(xlim=(0, WIDTH-1), ylim=(0, HEIGHT-1))
im = ax.imshow(current_grid, interpolation='nearest', cmap=pyplot.cm.gray)
ani = animation.FuncAnimation(fig, update_grid, interval=50, blit=True)
pyplot.show()
