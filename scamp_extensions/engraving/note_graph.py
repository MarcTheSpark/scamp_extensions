"""
Module containing the :class:`PartNoteGraph` class, which makes it possible to draw the notes of a
:class:`~scamp.performance.PerformancePart` to an SVG file. Ultimately, I plan to make it so that you
can save a whole Performance to an SVG file or even to a PDF.
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
from numbers import Real
from typing import Tuple, Callable, Sequence
from scamp import EnvelopeSegment, Performance, PerformancePart
import drawSvg


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
    :param time_range: time range to map horizontal space to; defaults to 0 to length of part
    :param fill_color: the fill color of note glyphs; overridden by color parameter, if active
    :param outline_color: note outline color
    :param outline_width: note outline width
    :param guide_lines: the values of the height parameter at which to draw horizontal guide lines.
    :param guide_line_width: width of the guide lines
    :param guide_line_color: color of the guide lines
    :param attack_only: if true, only draw the attack of each note as a circle.
    """

    def __init__(self, performance_part: PerformancePart, height_parameter: str = "pitch",
                 height_parameter_range: Tuple[Real, Real] = None,  width_parameter: str = "volume",
                 width_parameter_range: Tuple[Real, Real] = None, width_range: Tuple[Real, Real] = (1, 20),
                 color_parameter: str = None, color_parameter_range: Tuple[Real, Real] = None,
                 color_map: Callable[[Real], Tuple[Real, Real, Real]] = default_color_map,
                 time_range: Tuple[Real, Real] = None, fill_color: str = "black", outline_color: str = "black",
                 outline_width: Real = 1, guide_lines: Sequence[Real] = (), guide_line_width: Real = 2,
                 guide_line_color: str = 'black', attack_only: bool = False):

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
        self.guide_lines = guide_lines
        self.guide_line_width = guide_line_width
        self.guide_line_color = guide_line_color

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
            height_envelope = height.duplicate() if isinstance(height, Envelope) else Envelope((height, height), (note.length_sum(),))
            height_envelope.remove_segments_after(note.length_sum())
            height_envelope.shift_vertical(-self.height_parameter_range[0])
            height_envelope.scale_vertical(dimensions[1] / (self.height_parameter_range[1] - self.height_parameter_range[0]))
            height_envelope.shift_vertical(bottom_left[1])
            height_envelope.scale_horizontal(dimensions[0] / (self.time_range[1] - self.time_range[0]))
            height_envelope.shift_horizontal(bottom_left[0] + dimensions[0] * (note.start_beat - self.time_range[0]) /
                                             (self.time_range[1] - self.time_range[0]))

            width = note.pitch if self.width_parameter == "pitch" \
                else note.volume if self.width_parameter == "volume" \
                else note.properties["param_" + self.width_parameter] \
                if ("param_" + self.width_parameter) in note.properties else 0
            width_envelope = width.duplicate() if isinstance(width, Envelope) else Envelope((width, width), (note.length_sum(),))
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
                    else note.properties.extra_playback_parameters[self.color_parameter] \
                    if self.color_parameter in note.properties.extra_playback_parameters else 0
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
        self._render_guide_lines(drawing, bottom_left, dimensions)

    def _render_guide_lines(self, drawing: drawSvg.Drawing, bottom_left: Tuple[Real, Real],
                            dimensions: Tuple[Real, Real]):
        for value in self.guide_lines:
            line_height = bottom_left[1] + (value - self.height_parameter_range[0]) / \
                          (self.height_parameter_range[1] - self.height_parameter_range[0]) * dimensions[1]
            drawing.append(
                drawSvg.Line(
                    bottom_left[0], line_height, bottom_left[0] + dimensions[0], line_height,
                    stroke_width=self.guide_line_width, stroke=self.guide_line_color
                )
            )

    def render_to_file(self, file_path, dimensions, bg_color=None, h_padding=100, v_padding=100, pixel_scale=2):
        unpadded_dimensions = dimensions[0] - 2 * h_padding, dimensions[1] - 2 * v_padding
        d = drawSvg.Drawing(*dimensions, displayInline=False)
        if bg_color is not None:
            d.append(drawSvg.Rectangle(0, 0, *dimensions, fill=bg_color))
        self.render(d, (h_padding, v_padding), unpadded_dimensions)
        d.setPixelScale(pixel_scale)
        d.saveSvg(file_path)
