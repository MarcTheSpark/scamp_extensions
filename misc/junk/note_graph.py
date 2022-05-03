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
from numbers import Real
from typing import Tuple, Callable

from scamp import *
import drawSvg


# d = drawSvg.Drawing(200, 100, origin='center', displayInline=False)
#
# # Draw an irregular polygon
# d.append(drawSvg.Lines(-80, -45,
#                        70, -49,
#                        95, 49,
#                        -90, 40,
#                        close=True,
#                        fill='#eeee00',
#                        stroke='black'))
#
# d.append(drawSvg.Circle(-40, -10, 30,
#                         fill='red', stroke_width=2, stroke='black'))

# # Draw a rectangle
# r = drawSvg.Rectangle(-80,0,40,50, fill='#1248ff')
# r.appendTitle("Our first rectangle")  # Add a tooltip
# d.append(r)
#
# # Draw a circle
# d.append(drawSvg.Circle(-40, -10, 30,
#             fill='red', stroke_width=2, stroke='black'))
#
# # Draw an arbitrary path (a triangle in this case)
# p = drawSvg.Path(stroke_width=2, stroke='lime',
#               fill='black', fill_opacity=0.2)
# p.M(-10, 20)  # Start path at point (-10, 20)
# p.C(30, -10, 30, 50, 70, 20)  # Draw a curve to (70, 20)
# d.append(p)
#
# # Draw text
# d.append(drawSvg.Text('Basic text', 8, -10, 35, fill='blue'))  # Text with font size 8
# d.append(drawSvg.Text('Path text', 8, path=p, text_anchor='start', valign='middle'))
# d.append(drawSvg.Text(['Multi-line', 'text'], 8, path=p, text_anchor='end'))
#
# # Draw multiple circular arcs
# d.append(drawSvg.ArcLine(60,-20,20,60,270,
#             stroke='red', stroke_width=5, fill='red', fill_opacity=0.2))
# d.append(drawSvg.Arc(60,-20,20,60,270,cw=False,
#             stroke='green', stroke_width=3, fill='none'))
# d.append(drawSvg.Arc(60,-20,20,270,60,cw=True,
#             stroke='blue', stroke_width=1, fill='black', fill_opacity=0.3))
#
# # Draw arrows
# arrow = drawSvg.Marker(-0.1, -0.5, 0.9, 0.5, scale=4, orient='auto')
# arrow.append(drawSvg.Lines(-0.1, -0.5, -0.1, 0.5, 0.9, 0, fill='red', close=True))
# p = drawSvg.Path(stroke='red', stroke_width=2, fill='none',
#               marker_end=arrow)  # Add an arrow to the end of a path
# p.M(20, -40).L(20, -27).L(0, -20)  # Chain multiple path operations
# d.append(p)
# d.append(drawSvg.Line(30, -20, 0, -10,
#             stroke='red', stroke_width=2, fill='none',
#             marker_end=arrow))  # Add an arrow to the end of a line

# d.setPixelScale(2)  # Set number of pixels per geometry unit
# d.saveSvg('example.svg')





# d = drawSvg.Drawing(4000, 300, displayInline=False)
#
#
# def draw_part_note_graph(svg_draw: drawSvg.Drawing, performance_part: PerformancePart,
#                          lower_left: Tuple[float, float], dimensions: Tuple[float, float],
#                          pitch_range: Tuple[float, float] = None):
#     if pitch_range is None:
#         min_pitch = float("inf")
#         max_pitch = float("-inf")
#         for note in performance_part.get_note_iterator():
#             pitch_top = note.pitch.max_level() if isinstance(note.pitch, Envelope) else note.pitch
#             pitch_bottom = note.pitch.min_level() if isinstance(note.pitch, Envelope) else note.pitch
#             if pitch_top > max_pitch:
#                 max_pitch = pitch_top
#             if pitch_bottom < min_pitch:
#                 min_pitch = pitch_bottom
#     else:
#         min_pitch, max_pitch = pitch_range
#
#     for note in performance_part.get_note_iterator():
#         start_pitch = note.pitch.start_level() if isinstance(note.pitch, Envelope) else note.pitch
#         svg_draw.append(
#             drawSvg.Circle(lower_left[0] + dimensions[0] * note.start_beat / performance_part.end_beat,
#                            lower_left[1] + dimensions[1] * (start_pitch - min_pitch) / (max_pitch - min_pitch),
#                            5 * note.volume, fill='black')
#         )
#
#
# perf = Performance.load_from_json("fives.json")
# draw_part_note_graph(d, perf.parts[0], (50, 50), (4000, 200))
# # draw_part_note_graph(d, perf.parts[1], (50, 50), (600, 200))
#
# d.setPixelScale(2)  # Set number of pixels per geometry unit
# d.saveSvg('example.svg')


from scamp import Envelope

# -------------------------------------------------- Color/gradients --------------------------------------------------

_default_cm_envelope_red = Envelope.from_levels((0, 0, 78, 151, 211, 250, 255, 255, 255))
_default_cm_envelope_green = Envelope.from_levels((0, 0, 0, 0, 0, 30, 170, 250, 255))
_default_cm_envelope_blue = Envelope.from_levels((0, 81, 122, 118, 64, 0, 0, 97, 255))


def default_color_map(intensity):
    return _default_cm_envelope_red.value_at(intensity), \
           _default_cm_envelope_green.value_at(intensity), \
           _default_cm_envelope_blue.value_at(intensity)


def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(int(x) for x in rgb)


def make_intensity_gradient(envelope, start_x, end_x, color_map=default_color_map, value_range=None):
    envelope = envelope.duplicate()
    envelope.normalize_to_duration(1)
    if value_range is not None:
        envelope.shift_vertical(-value_range[0])
        envelope.scale_vertical(1/(value_range[1] - value_range[0]))

    # subdivide envelope segments until none of them are covering more than 0.1 in range
    gaps_too_big = True
    while gaps_too_big:
        gaps_too_big = False
        for segment in envelope.segments:
            if abs(segment.end_level - segment.start_level) > 0.1:
                envelope.insert_interpolated((segment.start_time + segment.end_time) / 2)
                gaps_too_big = True

    grad = drawSvg.LinearGradient(start_x, 0, end_x, 0)
    for segment in envelope.segments:
        grad.addStop(segment.start_time, rgb_to_hex(color_map(segment.start_level)))
    grad.addStop(1, rgb_to_hex(color_map(envelope.end_level())))
    return grad


def get_fill(parameter, start_x, end_x, color_map=default_color_map, value_range=None):
    if isinstance(parameter, Envelope):
        return make_intensity_gradient(parameter, start_x, end_x, color_map, value_range)
    else:
        return rgb_to_hex(color_map(
            parameter if value_range is None else (parameter - value_range[0]) / (value_range[1] - value_range[0])
        ))


# -------------------------------------------------- Draw note --------------------------------------------------


def _get_unit_slope_vector(slope):
    return 1 / (slope ** 2 + 1) ** 0.5, slope / (slope ** 2 + 1) ** 0.5


def _get_segment_raw(height_segment: EnvelopeSegment, width_segment: EnvelopeSegment, fill,
                     outline_width, outline_color):
    """Returns the shape of a single envelope segment as a list of three drawing elements (fill and both outlines)"""
    p1 = height_segment.start_time, height_segment.start_level
    p4 = height_segment.end_time, height_segment.end_level
    dist = ((height_segment.end_time - height_segment.start_time) ** 2 +
            (height_segment.end_level - height_segment.start_level) ** 2) ** 0.5 / 3

    start_slope = height_segment.start_slope()
    start_unit_slope_vector = _get_unit_slope_vector(start_slope)
    start_unit_normal_vector = - start_unit_slope_vector[1], start_unit_slope_vector[0]
    p2 = height_segment.start_time + dist * start_unit_slope_vector[0], \
         height_segment.start_level + dist * start_unit_slope_vector[1]

    end_slope = height_segment.end_slope()
    end_unit_slope_vector = _get_unit_slope_vector(end_slope)
    end_unit_normal_vector = - end_unit_slope_vector[1], end_unit_slope_vector[0]
    p3 = height_segment.end_time - dist * end_unit_slope_vector[0], \
         height_segment.end_level - dist * end_unit_slope_vector[1]

    start_a = p1[0] + start_unit_normal_vector[0] * width_segment.start_level,\
              p1[1] + start_unit_normal_vector[1] * width_segment.start_level
    start_b = p1[0] - start_unit_normal_vector[0] * width_segment.start_level,\
              p1[1] - start_unit_normal_vector[1] * width_segment.start_level
    control_1a = p2[0] + start_unit_normal_vector[0] * width_segment.value_at(width_segment.start_time + width_segment.duration / 3),\
                 p2[1] + start_unit_normal_vector[1] * width_segment.value_at(width_segment.start_time + width_segment.duration / 3)
    control_1b = p2[0] - start_unit_normal_vector[0] * width_segment.value_at(width_segment.start_time + width_segment.duration / 3),\
                 p2[1] - start_unit_normal_vector[1] * width_segment.value_at(width_segment.start_time + width_segment.duration / 3)
    control_2a = p3[0] + end_unit_normal_vector[0] * width_segment.value_at(width_segment.start_time + width_segment.duration * 2 / 3),\
                 p3[1] + end_unit_normal_vector[1] * width_segment.value_at(width_segment.start_time + width_segment.duration * 2 / 3)
    control_2b = p3[0] - end_unit_normal_vector[0] * width_segment.value_at(width_segment.start_time + width_segment.duration * 2 / 3),\
                 p3[1] - end_unit_normal_vector[1] * width_segment.value_at(width_segment.start_time + width_segment.duration * 2 / 3)
    end_a = p4[0] + end_unit_normal_vector[0] * width_segment.end_level,\
            p4[1] + end_unit_normal_vector[1] * width_segment.end_level
    end_b = p4[0] - end_unit_normal_vector[0] * width_segment.end_level,\
            p4[1] - end_unit_normal_vector[1] * width_segment.end_level

    return [
        drawSvg.Path(fill=fill, close=True, stroke='none').
            M(*start_a).C(*control_1a, *control_2a, *end_a).L(*end_b).
            C(*control_2b, *control_1b, *start_b).L(*start_a),
        drawSvg.Path(stroke=outline_color, stroke_width=outline_width, fill='none').
            M(*start_a).C(*control_1a, *control_2a, *end_a),
        drawSvg.Path(stroke=outline_color, stroke_width=outline_width, fill='none').
            M(*start_b).C(*control_1b, *control_2b, *end_b),
    ]


def _draw_note_raw(draw: drawSvg.Drawing, height_envelope: Envelope, width_envelope: Envelope, fill,
                   outline_width, outline_color):
    """
    Draws a note shape, based on envelopes in drawing coordinates.

    :param draw: the drawSvg.Drawing used
    :param height_envelope: an envelope representing the curve itself, normalized to drawing coordinates
    :param width_envelope:  an envelope representing the curve width, normalized to drawing coordinates
    :param fill: the color or gradient to use
    :param outline_width: width of the stroke outline of the note
    :param outline_color: color of the outline of the note
    """
    key_points = set(height_envelope.times).union(set(width_envelope.times))
    for t in key_points:
        height_envelope.insert_interpolated(t)
        width_envelope.insert_interpolated(t)

    outlines = []
    fill_chunks = []

    fill_chunks.append(drawSvg.Circle(height_envelope.end_time(), height_envelope.end_level(),
                                      width_envelope.end_level(), fill=fill, stroke="none"))
    outlines.append(drawSvg.Circle(height_envelope.end_time(), height_envelope.end_level(),
                                   width_envelope.end_level(), fill="none", stroke=outline_color,
                                   stroke_width=outline_width))
    for height_segment, width_segment in zip(height_envelope.segments, width_envelope.segments):
        fill_chunks.append(drawSvg.Circle(height_segment.start_time, height_segment.start_level,
                                          width_segment.start_level, fill=fill, stroke="none"))
        outlines.append(drawSvg.Circle(height_segment.start_time, height_segment.start_level, width_segment.start_level,
                                       fill='none', stroke=outline_color, stroke_width=outline_width))
        fill_chunk, *segment_outlines = _get_segment_raw(height_segment, width_segment, fill,
                                                         outline_width, outline_color)
        fill_chunks.append(fill_chunk)
        outlines.extend(segment_outlines)
    draw.extend(outlines)
    draw.extend(fill_chunks)


def _draw_note_attack_only(draw: drawSvg.Drawing, height_envelope: Envelope, width_envelope: Envelope, fill,
                           outline_width, outline_color):
    """
    Draws just the attack of a note shape, based on envelopes in drawing coordinates.

    :param draw: the drawSvg.Drawing used
    :param height_envelope: an envelope representing the curve itself, normalized to drawing coordinates
    :param width_envelope:  an envelope representing the curve width, normalized to drawing coordinates
    :param fill: the color or gradient to use
    :param outline_width: width of the stroke outline of the note
    :param outline_color: color of the outline of the note
    """
    draw.append(
        drawSvg.Circle(height_envelope.start_time(), height_envelope.start_level(),
                       width_envelope.start_level(), fill=fill, stroke=outline_color, stroke_width=outline_width)
    )


class PartNoteGraph:

    """
    Class that takes a performance part and a bunch of drawing/visualization settings,
    and can render to a `class:svgDraw.Drawing`.

    :param performance_part: the PerformancePart on which to base this note graph
    :param height_parameter: the playback parameter of that governs each note's height on the graph; defaults to pitch
    :param height_parameter_range: range of values expected from the parameter that governs height. If the parameter is
        pitch, defaults to the min and max pitch found in the part. Otherwise defaults to (0, 1).
    :param width_parameter: the playback parameter of that governs each note's width on the graph; defaults to volume
    :param width_parameter_range: range of values expected from the parameter that governs width. If the parameter is
        pitch, defaults to the min and max pitch found in the part. Otherwise defaults to (0, 1).
    :param width_range: range of note widths mapped to in the drawing
    :param color_parameter: the parameter governing note color, if any (overrides fill_color); inactive by default
    :param color_parameter_range: range of values expected from the parameter that governs color. If the parameter is
        pitch, defaults to the min and max pitch found in the part. Otherwise defaults to (0, 1).
    :param color_map: function from the interval [0, 1] to an RGB color tuple, where 0 represents the color
        parameter at the bottom of its range and 1 at the top.
    :param pitch_range: range of pitches to map vertical space to; defaults to min and max pitch of the part.
    :param time_range: time range to map horizontal space to; defaults to 0 to length of part
    :param fill_color: the fill color of note glyphs; overridden by color parameter, if active
    :param outline_color: note outline color
    :param outline_width: note outline width
    """

    def __init__(self, performance_part: PerformancePart, height_parameter: str = "pitch",
                 height_parameter_range: Tuple[Real, Real] = None,  width_parameter: str = "volume",
                 width_parameter_range: Tuple[Real, Real] = None, width_range: Tuple[Real, Real] = (1, 20),
                 color_parameter: str = None, color_parameter_range: Tuple[Real, Real] = None,
                 color_map: Callable[[Real], Tuple[Real, Real, Real]] = default_color_map,
                 time_range: Tuple[Real, Real] = None, fill_color: str = "black", outline_color: str = "black",
                 outline_width: Real = 1, attack_only: bool = False):

        self.performance_part = performance_part
        self.height_parameter = height_parameter
        self.height_parameter_range = height_parameter_range if height_parameter_range is not None \
            else self._get_part_pitch_range() if height_parameter == "pitch" else (0, 1)
        self.width_parameter = width_parameter
        self.width_parameter_range = width_parameter_range if width_parameter_range is not None \
            else self._get_part_pitch_range() if width_parameter == "pitch" else (0, 1)
        self.width_range = width_range
        self.color_parameter = color_parameter
        self.color_parameter_range = color_parameter_range if color_parameter_range is not None \
            else self._get_part_pitch_range() if color_parameter == "pitch" else (0, 1)
        self.color_map = color_map
        self.time_range = (0, performance_part.end_beat) if time_range is None else time_range
        self.fill_color = fill_color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.attack_only = attack_only

    def _get_part_pitch_range(self):
        return min(note.pitch.min_level() if isinstance(note.pitch, Envelope) else note.pitch
                   for note in self.performance_part.get_note_iterator()),\
               max(note.pitch.max_level() if isinstance(note.pitch, Envelope) else note.pitch
                   for note in self.performance_part.get_note_iterator())

    def render(self, drawing: drawSvg.Drawing, bottom_left: Tuple[Real, Real], dimensions: Tuple[Real, Real]):
        for note in self.performance_part.get_note_iterator():
            height = note.pitch if self.height_parameter == "pitch" \
                else note.volume if self.height_parameter == "volume" \
                else note.properties["param_" + self.height_parameter] \
                if ("param_" + self.height_parameter) in note.properties else 0
            height_envelope = height.duplicate() if isinstance(height, Envelope) else Envelope((height,), (note.length_sum(),))
            height_envelope.remove_segments_after(note.length_sum())
            height_envelope.shift_vertical(-self.height_parameter_range[0])
            height_envelope.scale_vertical(dimensions[1] / (self.height_parameter_range[1] - self.height_parameter_range[0]))
            height_envelope.scale_horizontal(dimensions[0] / (self.time_range[1] - self.time_range[0]))
            height_envelope.shift_horizontal(bottom_left[0] + dimensions[0] * (note.start_beat - self.time_range[0]) /
                                             (self.time_range[1] - self.time_range[0]))

            width = note.pitch if self.width_parameter == "pitch" \
                else note.volume if self.width_parameter == "volume" \
                else note.properties["param_" + self.width_parameter] \
                if ("param_" + self.width_parameter) in note.properties else 0
            width_envelope = width.duplicate() if isinstance(width, Envelope) else Envelope((width,), (note.length_sum(),))
            width_envelope.remove_segments_after(note.length_sum())
            width_envelope.shift_vertical(-self.width_parameter_range[0])
            width_envelope.scale_vertical((self.width_range[1] - self.width_range[0]) /
                                           (self.width_parameter_range[1] - self.width_parameter_range[0]))
            width_envelope.shift_vertical(self.width_range[0])
            width_envelope.scale_horizontal(dimensions[0] / (self.time_range[1] - self.time_range[0]))
            width_envelope.shift_horizontal(bottom_left[0] + dimensions[0] * (note.start_beat - self.time_range[0]) /
                                            (self.time_range[1] - self.time_range[0]))

            if self.color_parameter is not None:
                color = note.pitch if self.color_parameter == "pitch" \
                    else note.volume if self.color_parameter == "volume" \
                    else note.properties["param_" + self.color_parameter] \
                    if ("param_" + self.color_parameter) in note.properties else 0
                note_fill = get_fill(color, height_envelope.start_time(), height_envelope.end_time(),
                                     self.color_map, self.color_parameter_range)
            else:
                note_fill = self.fill_color
            if self.attack_only:
                _draw_note_attack_only(drawing, height_envelope, width_envelope, note_fill, self.outline_width,
                                       self.outline_color)
            else:
                _draw_note_raw(drawing, height_envelope, width_envelope, note_fill, self.outline_width,
                               self.outline_color)


d = drawSvg.Drawing(2000, 500, displayInline=False)
# rect = drawSvg.Rectangle(200, 100, 250, 150,
#                          fill=get_fill(Envelope([50, 60, 40], [3, 7]), 200, 450, value_range=(-10, 60)))
# d.append(rect)

# d.extend(_get_segment_raw(EnvelopeSegment(100, 400, 2, 9, 0), EnvelopeSegment(100, 400, 300, 100, 3),
#                           fill=get_fill(Envelope([50, 60, 40], [3, 7]), 100, 400, value_range=(-10, 60))))

d.append(drawSvg.Rectangle(0, 0, 2000, 500, fill='gray'))

PartNoteGraph(Performance.load_from_json("sines.json").parts[0], width_range=(0.5, 9),
              color_parameter="vibFreq", color_parameter_range=(0, 15), attack_only=True).render(d, (0, 100), (2000, 300))


# _draw_note_raw(d, Envelope([200, 400, 100], [100, 200], curve_shapes=[-52, -20], offset=50),
#                Envelope([1, 50], [300], offset=50),
#                fill=get_fill(Envelope([50, 60, 10], [3, 7]), 50, 350, value_range=(-10, 60)))


d.setPixelScale(2)  # Set number of pixels per geometry unit
d.saveSvg('example.svg')

exit()

# es = EnvelopeSegment(2, 5, 60, 67, curve_shape=4)
# print(es.start_slope(), es.end_slope())
# es.show_plot()

env = Envelope([10, 70, 30, 120, 20, 90], [40, 80, 30, 40, 40], curve_shapes=[2, 3, -2, -8, 5])
env.show_plot()

d = drawSvg.Drawing(500, 500, displayInline=False)

p = drawSvg.Path(stroke="black", stroke_width=1, fill='none')

env = env.duplicate()
for segment in tuple(env.segments):
    env.insert_interpolated((segment.start_time + segment.end_time) / 2)
for segment in tuple(env.segments):
    env.insert_interpolated((segment.start_time + segment.end_time) / 2)

for segment in env.segments:
    p1 = segment.start_time, segment.start_level
    p4 = segment.end_time, segment.end_level
    dist = ((segment.end_time - segment.start_time) ** 2 +
            (segment.end_level - segment.start_level) ** 2) ** 0.5 / 3

    slope = segment.start_slope()
    p2 = segment.start_time + dist / (slope ** 2 + 1) ** 0.5, \
         segment.start_level + dist * slope / (slope ** 2 + 1) ** 0.5
    # p2 = segment.start_time + third_time, segment.start_level + third_time * segment.start_slope()
    slope = segment.end_slope()
    p3 = segment.end_time - dist / (slope ** 2 + 1) ** 0.5, \
         segment.end_level - dist * slope / (slope ** 2 + 1) ** 0.5

    # p3 = segment.start_time + 2 * third_time, segment.end_level - third_time * segment.end_slope()
    # print(segment.start_slope(), segment.end_slope(), p1, p2, p3, p4)
    p.M(*p1).C(*p2, *p3, *p4)
    # d.append(drawSvg.Circle(*p1, 2))
    # d.append(drawSvg.Circle(*p2, 2))
    # d.append(drawSvg.Circle(*p3, 2))
    # d.append(drawSvg.Circle(*p4, 2))

d.append(p)
d.setPixelScale(2)  # Set number of pixels per geometry unit
d.saveSvg('example.svg')


exit()
d = drawSvg.Drawing(500, 500, displayInline=False)
p = drawSvg.Path(stroke="black", stroke_width=3, fill='none').m(50, 50).c(100, 100, 150, 100, 200, 50)
d.append(
    p
)
d.append(drawSvg.Circle(50, 50, 4))
d.append(drawSvg.Circle(100, 100, 4))
d.append(drawSvg.Circle(150, 100, 4))
d.append(drawSvg.Circle(200, 50, 4))
d.setPixelScale(2)  # Set number of pixels per geometry unit
d.saveSvg('example.svg')
