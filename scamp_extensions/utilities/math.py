"""
Subpackage containing mathematical utility functions (many of which are imported from :mod:`scamp.utilities`.
"""

from scamp.utilities import is_x_pow_of_y, floor_x_to_pow_of_y, ceil_x_to_pow_of_y, round_x_to_pow_of_y, \
    floor_to_multiple, ceil_to_multiple, round_to_multiple, is_multiple, prime_factor, is_prime
from math import gcd


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)
