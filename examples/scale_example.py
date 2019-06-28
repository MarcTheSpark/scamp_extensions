from scamp import *
from scamp_extensions.pitch import Scale

s = Session()
clarinet = s.new_part("clarinet")

scales = [
    Scale([48, 50, 52, 53, 55, 57, 59, 60], True),  # major
    Scale([48, 51, 53, 54, 55, 58, 60], True),  # blues
    Scale([48, 50], True),  # whole tone
    Scale([48, 50, 51], True),  # octatonic
    Scale([48, 51.0185, 52.3508, 53.8251, 56.8436, 58.1760,
           61.1944, 62.6687, 65.6872, 67.0196], True)  # Bohlen-Pierce
]

for scale in scales:
    for scale_degree in range(0, 16):
        clarinet.play_note(scale.degree_to_pitch(scale_degree), 1.0, 0.25)

    for scale_degree in range(0, 16):
        clarinet.play_chord([scale.degree_to_pitch(x) for x in range(scale_degree, scale_degree + 5, 2)], 1.0, 0.25)
