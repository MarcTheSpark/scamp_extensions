from scamp import *
from scamp_extensions.pitch import Scale, ScaleType

s = Session()
clarinet = s.new_part("clarinet")

scales = [
    Scale.from_pitches([48, 51, 53, 54, 55, 58, 60]),  # blues
    Scale.locrian(58),
    Scale(ScaleType(26., 104., Fraction(3, 2), (600., Fraction(5, 4)), 2, (204., 2)), 55),
    Scale.from_pitches([48, 50, 51]),  # octatonic
    Scale.from_start_pitch_and_cent_or_ratio_intervals(55, ["200.", "5/4", "200., 5/4", "3/2", "7/4", "2"]),
    Scale.from_scala_file("data/bohlen_12.scl", 48)
]

for scale in scales:
    for scale_degree in range(0, 16):
        clarinet.play_note(scale.degree_to_pitch(scale_degree), 1.0, 0.25)

    for scale_degree in range(0, 16):
        clarinet.play_chord([scale.degree_to_pitch(x) for x in range(scale_degree, scale_degree + 5, 2)], 1.0, 0.25)
