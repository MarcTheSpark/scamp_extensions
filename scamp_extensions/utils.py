import math


# ----------------------------------------------- Pitch Space Conversions ---------------------------------------------

def ratio_to_cents(ratio):
    return math.log2(ratio) * 1200


def cents_to_ratio(cents):
    return math.pow(2, cents / 1200)


def midi_to_hertz(midi_value, A=440):
    return A * math.pow(2, (midi_value - 69) / 12)


def hertz_to_midi(hertz_value, A=440):
    return 12 * math.log2(hertz_value / A) + 69


# from Terhardt. Chosen for ease of inverse calculation
def freq_to_bark(f):
    return 13.3 * math.atan(0.75*f/1000.0)


# the inverse formula
def bark_to_freq(b):
    return math.tan(b/13.3)*1000.0/0.75
