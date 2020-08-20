"""
Module containing implementations of many of Clarence Barlow's theoretical constructs. These include:

    - Indigestibility
    - Harmonicity (including harmonicity-based scale rationalization)
    - Rhythmic indispensability
    - Metric Coherence
    
All of these are described in his book, "On Musiquantics".
(http://clarlow.org/wp-content/uploads/2016/10/On-MusiquanticsA4.pdf)
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

import math
import itertools
from fractions import Fraction
from functools import reduce
from typing import Sequence, Tuple, Union, TypeVar

# ---------------------------------------------- Utility Functions -------------------------------------------------


# decorator that saves function output
def _save_answers(func):
    func.answers = {}

    def func_wrapper(*args):
        t_args = tuple(args)
        if t_args in func.answers:
            return func.answers[t_args]
        else:
            ans = func(*args)
            func.answers[t_args] = ans
            return ans

    return func_wrapper


def _gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b
    return a


def _lcm(a, b):
    """Return lowest common multiple."""
    return a * b // _gcd(a, b)


def _is_prime(a):
    """Determine if the given number is prime."""
    return not (a < 2 or any(a % x == 0 for x in range(2, int(a ** 0.5) + 1)))


def _prime_factor(n):
    """Returns a list of prime factors of the given number"""
    i = 2
    primes = []
    while i * i <= n:
        while n % i == 0:
            n //= i
            primes.append(i)
        i += 1

    if n != 1:
        primes.append(n)

    return primes


def _rotate(l, n):
    """Rotates a list in a circular fashion so that it starts from the nth index and wraps back around to the (n-1)st"""
    return l[n:] + l[:n]


def _get_nth_prime(n):
    """Returns the nth prime, where 2 counts as the zeroth prime."""
    # counting 2 as the 0th prime
    if n == 0:
        return 2

    if hasattr(_get_nth_prime, "primes"):
        assert isinstance(_get_nth_prime.primes, list)
        if n < len(_get_nth_prime.primes):
            return _get_nth_prime.primes[n]
        else:
            k = _get_nth_prime.primes[len(_get_nth_prime.primes) - 1] + 1
    else:
        _get_nth_prime.primes = [2]
        k = 3

    while len(_get_nth_prime.primes) <= n:
        # get the next prime
        found_a_prime = True
        for prime in _get_nth_prime.primes:
            if k % prime == 0:
                found_a_prime = False
                break
        if found_a_prime:
            _get_nth_prime.primes.append(k)
        else:
            k += 1

    return k


def _gaussian_discount(x, center, standard_deviation):
    """Returns a factor that decreases (according to a gaussian curve with the given standard deviation) as x
    gets farther from the specified center."""
    return math.exp(-(x-center)**2/(2*standard_deviation**2))


# ---------------------------------------- Indigestibility and Harmonicity ------------------------------------------


def indigestibility(n: int) -> float:
    """
    Returns a number representing how hard it is for a human to divide an object (e.g. cake, span of time) into n
    equal pieces. (See Clarence Barlow's "Musiquantics".)
    """
    if not isinstance(n, int) and n > 0:
        raise ValueError("n must be an integer greater than zero.")
    if _is_prime(n):
        return 2 * float((n-1)**2) / n
    else:
        total = 0
        for factor in _prime_factor(n):
            total += indigestibility(factor)
        return total


def harmonicity(p: int, q: int) -> float:
    """
    Returns a number representing the simplicity (and thereby a kind of consonance) of an interval with frequency
    ratio of p/q.
    """
    indig_p = indigestibility(p)
    indig_q = indigestibility(q)
    if indig_p + indig_q == 0:
        return float("inf")
    return math.copysign(1/(indig_p + indig_q), indig_q - indig_p)


# simply a translation of the equation from F25 in musiquantics
# the point is, not only is the min_harmonicity a restriction, so is the octave range, since any prime in
# the numerator must have some primes in the denominator to bring it back from the stratosphere

def _get_max_prime_power(the_prime, min_harmonicity, max_octave_range=8):
    numerator = max_octave_range + 1.0 / min_harmonicity
    denominator = 1 + math.log(256) / math.log(27) if the_prime == 2 else \
        indigestibility(the_prime) + math.log(the_prime) / math.log(2)
    return int(numerator / denominator)

# [(4, 3), (75, 56), (27, 20), (675, 512), (320, 243), (21, 16), 
# (256, 189), (49, 36), (72, 55), (15, 11), (64, 49), (512, 375)]
# [(4, 3), (75, 56), (27, 20), (675, 512), (320, 243), (21, 16), 
# (256, 189), (49, 36), (72, 55), (15, 11), (64, 49), (512, 375)]

# This is quicker because it first narrows down the possibilities for higher primes
# I think it could be made still quicker by splitting it up still more
# basically we are pitting the efficiency of itertools.product with the efficiency of checking fewer possibilities
# but using more python code
@_save_answers
def _get_candidate_prime_pool(min_harmonicity, high_low_cutoff=0.25):
    max_inharmonicity = 1.0 / min_harmonicity
    max_primes = []
    n = 0

    while indigestibility(_get_nth_prime(n)) < max_inharmonicity:
        # old system
        max_primes.append(_get_max_prime_power(_get_nth_prime(n), min_harmonicity))
        n += 1

    first_high_prime = int(len(max_primes)*high_low_cutoff)
    low_ranges = [range(0, x+1) for x in max_primes[:first_high_prime]]
    high_ranges = [range(0, x+1) for x in max_primes[first_high_prime:]]

    acceptable_high_prime_combos = []
    for primes in itertools.product(*high_ranges):
        val = 0
        for i, power in enumerate(primes):
            val += indigestibility(_get_nth_prime(i + first_high_prime)) * power
        if val < max_inharmonicity:
            acceptable_high_prime_combos.append(primes)

    acceptable_prime_combos = []
    for high_primes, low_primes in itertools.product(acceptable_high_prime_combos, itertools.product(*low_ranges)):
        primes = low_primes + high_primes
        val = 0
        for i, power in enumerate(primes):
            val += indigestibility(_get_nth_prime(i)) * power
        if val < max_inharmonicity:
            acceptable_prime_combos.append(primes)
    return acceptable_prime_combos


# generates all possible ratios within a cent range that satisfy a minimum harmonicity
def _generate_ratio_candidates(cent_range, min_harmonicity):
    cent_range_low, cent_range_high = cent_range
    ratio_candidates = []

    interval_lower_bound = 2**(cent_range_low/1200.0)
    interval_upper_bound = 2**(cent_range_high/1200.0)
    # generate a whole bunch of ratios in the neighborhood of this cent interval
    # the candidates are based on a given lower harmonicity threshold (0.04 is the most common that Clarence uses)
    prime_combos = _get_candidate_prime_pool(min_harmonicity)
    top_bottom_options = itertools.product(*[[True, False]]*len(prime_combos[0]))
    # if you put 2s on top, no need to put them on bottom, since they'd cancel
    # so for each prime type, it could be on top or bottom
    # THIS IS THE SLOW PART
    # could probably be made much more efficient with numpy
    for tops_and_bottoms in top_bottom_options:
        for prime_combo in prime_combos:
            top = 1
            bottom = 1
            for i, power in enumerate(prime_combo):
                if tops_and_bottoms[i]:
                    top *= _get_nth_prime(i) ** power
                else:
                    bottom *= _get_nth_prime(i) ** power
            if interval_lower_bound < float(top)/bottom < interval_upper_bound:
                ratio_candidates.append((top, bottom))
    return set(ratio_candidates)


# nominal tolerance applies a gaussian envelope whereby ratios that are the nominal tolerance away are discounted 95%
# this happens at 2.447 * the standard deviation, so standard dev = nominal_tolerance / 2.447
# also we'll only generate possibilities within the nominal tolerance, since more than 95% overwhelming
def _get_ratio_candidates(desired_cent_ratio, nominal_tolerance, min_harmonicity, num_candidates=None):
    ratio_candidates = _generate_ratio_candidates((desired_cent_ratio - nominal_tolerance,
                                                   desired_cent_ratio + nominal_tolerance), min_harmonicity)
    candidates_and_values = []
    for ratio in ratio_candidates:
        cent_ratio = math.log(float(ratio[0])/ratio[1])/math.log(2) * 1200
        discount = _gaussian_discount(cent_ratio, desired_cent_ratio, nominal_tolerance / 2.447)
        candidates_and_values.append((ratio, math.fabs(harmonicity(*ratio)) * discount))
    candidates_and_values.sort(key=lambda x : x[1], reverse=True)
    return [cv[0] for cv in candidates_and_values] if num_candidates is None else \
        [cv[0] for cv in candidates_and_values[:num_candidates]]


def _get_tuning_inharmonicity(the_tuning):
    total_inharmonicity = 0
    for interval in itertools.combinations(the_tuning, 2):
        # interval is something like ((27, 16), (15, 8))
        # what we want is to look at the absolute harmonicity of (15*16) / (27*8)
        # the Fraction class reduces it for us, probably pretty efficiently
        reduced_fraction = Fraction(interval[0][1]*interval[1][0], interval[0][0]*interval[1][1])
        total_inharmonicity += indigestibility(reduced_fraction.numerator) + \
                              indigestibility(reduced_fraction.denominator)
    return total_inharmonicity


def rationalize_scale(cents_values: Sequence[float], nominal_tolerance: float, min_harmonicity: float,
                      num_candidates: int, num_to_return: int = None,
                      write_pretty: bool = False) -> Union[Tuple[Sequence, float], Sequence[Tuple[Sequence, float]]]:
    """
    Uses Clarence Barlow's algorithms for scale rationalization to determine optimal rational tunings given an input
    scale in cents values. Candidate scales are generated by finding rational frequency ratios from the start note that
    satisfy the minimum harmonicity requirement, and that resolve to near the specified number of cents. The nominal
    tolerance specifies the maximum acceptable deviation from the desired cents value. Having generated interval
    candidates for each scale degree, all possible scales using these candidates are compared, resulting in a ranking
    from highest to lowest "specific harmonicity" (which is just a measure of how simple the intrascalar ratios are)..

    :param cents_values: An array of cent values for the pitches of the scale, all in reference to a distance from
        the first degree of the scale
    :param nominal_tolerance: Number of cents that ratio candidates are allowed to deviate from the specified cents
        value. (Intervals that fall further away also rank lower when choosing the top candidates.)
    :param min_harmonicity: Minimum harmonicity of intervals used to generate interval candidates.
    :param num_candidates: Number of alternative candidates considered for each interval.
    :param num_to_return: if None, we just return the best tuning (or a list of equally best tunings) and the
        specific harmonicity. If a number n, we return a list of the top n tunings as ordered pairs
        (tuning, harmonicity)
    :param write_pretty: if True, it returns a list fraction strings (easier to read); if false, a list of tuples
    :return: a list of (tuning, specific_harmonicity) tuples, if n > 1, otherwise just the (tuning, harmonicity)
        pair for the scale with greatest specific harmonicity.
    """
    candidates = []
    print("Generating Candidates...")
    for i, cent_value in enumerate(cents_values):
        print("  ...for scale degree", i+1)
        candidates.append(_get_ratio_candidates(cent_value, nominal_tolerance, min_harmonicity, num_candidates))

    number_of_tunings = reduce(lambda a, b: a*b, map(len, candidates))
    if number_of_tunings == 0:
        raise Exception("No available candidates for some scale degrees")
    else:
        print("Comparing all", number_of_tunings, "possible tunings...")
    # keeps a list of the best tunings (as long as the num_to_return)
    # each entry goes (tuning, inharmonicity) if num_to_return = n >= 1
    # otherwise, if num_to_return is None, we just keep a list of the best tunings, 
    # each having least_tuning_inharmonicity
    best_tunings = []
    # only used if we are just returning the best tuning(s)
    least_tuning_inharmonicity = float("inf")
    tunings_checked = 0
    for tuning_choice in itertools.product(*candidates):
        tuning_inharmonicity = _get_tuning_inharmonicity(tuning_choice)
        returnable_tuning = [str(t[0]) + "/" + str(t[1]) for t in tuning_choice] if write_pretty else tuning_choice
        if num_to_return is not None:
            # we want to get the best num_to_return tunings returned
            if len(best_tunings) < num_to_return:
                # if we haven't even collected enough tunings to return yet, just add this one in
                best_tunings.append((returnable_tuning, tuning_inharmonicity))
                # then sort based on inharmonicity
                best_tunings.sort(key=lambda x: x[1])
            else:
                # otherwise, see if it's good enough to make the leaderboard by checking it with the worst leader
                if tuning_inharmonicity < best_tunings[-1][1]:
                    best_tunings.append((returnable_tuning, tuning_inharmonicity))
                    best_tunings.sort(key=lambda x: x[1])
                    best_tunings.pop()
        else:
            # if num_to_return is None (the default), we just return the best, though we
            # return multiple possibilities if more than one best exists
            if tuning_inharmonicity < least_tuning_inharmonicity - 0.0001:
                # if this is the best one so far (by more than just float rounding error)
                best_tunings = [returnable_tuning]
                least_tuning_inharmonicity = tuning_inharmonicity
            elif abs(tuning_inharmonicity - least_tuning_inharmonicity) < 0.0001:
                # if this is identical to the best so far (within float rounding error)
                best_tunings.append(returnable_tuning)

        tunings_checked += 1
        if tunings_checked % 1000 == 0:
            print(tunings_checked, "tunings checked")

    if num_to_return is not None:
        return [(x, len(cents_values) * (len(cents_values) - 1) / y) for (x, y) in best_tunings]
    else:
        specific_harmonicity = len(cents_values) * (len(cents_values) - 1) / least_tuning_inharmonicity
        if len(best_tunings) > 1:
            return best_tunings, specific_harmonicity
        else:
            return best_tunings[0], specific_harmonicity


# EXAMPLES!

# MAJOR SCALE
# print(rationalize_scale([0, 200, 400, 500, 700, 900, 1100, 1200], 40, 0.03, 3))
# HARMONIC MINOR SCALE
# print(rationalize_scale([0, 200, 300, 500, 700, 800, 1100, 1200], 40, 0.03, 3))
# PENTATONIC SCALE
# print(rationalize_scale([0, 200, 400, 700, 900, 1200], 40, 0.03, 3))
# WHOLE-TONE SCALE
# print(rationalize_scale([0, 200, 400, 600, 800, 1000, 1200], 40, 0.03, 3))
# NOTE: Fascinatingly, for the whole tone scale, there there are two identical best tunings with the exact same
# specific harmonicity. There's the one listed in the book (1/1, 10/9, 5/4, 64/45, 8/5, 16/9, 2/1), but there's
# also (1/1, 9/8, 5/4, 45/32, 8/5, 9/5, 2/1)
# BOHLEN-PIERCE #1
# print(rationalize_scale([0, 146, 293, 439, 585, 732, 878, 1024, 1170, 1317, 1463, 1609, 1756, 1902], 40, 0.04, 2))
# BOHLEN-PIERCE #2
# print(rationalize_scale([0, 146, 293, 439, 585, 732, 878, 1024, 1170, 1317, 1463, 1609, 1756, 1902], 20, 0.05, 2))
# CHROMATIC
# print(rationalize_scale([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200], 30, 0.04, 2, 4))
# Note that there are some discrepancies here: one of the reasons is that (probably due to rounding) I get
#    different candidates for the 10th scale degree and 9/5 is the third, and therefore doesn't make the cut
# print(_get_ratio_candidates(1000, 30, 0.04, 5))
# COMPARE: my program's ideal tuning, the tuning from Musiquantics, 
#   and the tuning from Musiquantics with 16/9 substituted for 9/5
# print(_get_tuning_inharmonicity(((1, 1), (16, 15), (10, 9), (6, 5), (5, 4), (4, 3),
#                                 (64, 45), (3, 2), (8, 5), (5, 3), (16, 9), (15, 8), (2, 1))), 
#       _get_tuning_inharmonicity(((1, 1), (16, 15), (9, 8), (6, 5), (5, 4), (4, 3),
#                                 (45, 32), (3, 2), (8, 5), (5, 3), (9, 5), (15, 8), (2, 1))), 
#       _get_tuning_inharmonicity(((1, 1), (16, 15), (9, 8), (6, 5), (5, 4), (4, 3),
#                                 (45, 32), (3, 2), (8, 5), (5, 3), (16, 9), (15, 8), (2, 1))))
# Fascinatingly, my tuning and the tuning from Musiquantics have identical Specific Harmonicities!
# But if you take the Musiquantics tuning and substitute 16/9 it doesn't like it. (Doesn't really fit with the scale.)
# ALSO: if we use Nominal tolerance 40, the 9/5 is included and we get it as well
# print rationalize_scale([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200], 40, 0.04, 2)

# ---------------------------------------------- indispensability -----------------------------------------------


def _decompose_to_twos_and_threes(n):
    assert isinstance(n, int)
    out = []
    if n % 2 == 1:
        n -= 3
        out.append(3)

    while n > 0:
        n -= 2
        out.append(2)

    out.reverse()
    return out


def _first_order_backward_beat_priorities(length):
    if hasattr(length, "__getitem__"):
        # a list or tuple or suchlike means we're dealing with additive meter
        # first reverse the group lengths, since we are doing everything backwards
        # lets take the example of length = (3, 5, 2)
        group_lengths = length[::-1]
        # now group_lengths = (2, 5, 3), since we calculate backwards

        # then construct beat groups according to their (backwards) position in the bar
        beat_groups = []
        beat = 0
        for group in group_lengths:
            beat_group = []
            for i in range(group):
                beat_group.append(beat)
                beat += 1
            beat_groups.append(beat_group)
        # in our example, this results in beat_groups = [[0, 1], [2, 3, 4, 5, 6], [7, 8, 9]]

        # OK, now we move the beats to a list in order from most indispensable to least
        order_of_indispensability = []

        # first take the first of each group (these are the beats)
        for beat_group in beat_groups:
            order_of_indispensability.append(beat_group.pop(0))
        # example: order_of_indispensability = [0, 2, 7]

        # then gradually pick all the beats
        # beat groups that are the longest get whittled away first, until they
        # are no longer than any of the others. Always we go in order (backwards through the bar)
        # example: 3, 4, 5 get added next (remember, it's backwards, so we're adding the pulses
        #   leading up to the beat following the 5 group) once there are equally many pulses left
        #   in each beat, we add from each group in order (i.e. backwards order).
        largest_beat_group_length = max([len(x) for x in beat_groups])
        while largest_beat_group_length > 0:
            for beat_group in beat_groups:
                if len(beat_group) == largest_beat_group_length:
                    order_of_indispensability.append(beat_group.pop(0))
            largest_beat_group_length = max([len(x) for x in beat_groups])

        return order_of_indispensability
    else:
        return range(length)


def _get_backward_beat_priorities(*args):
    strata_backward_beat_priorities = []
    for meter_stratum in args:
        strata_backward_beat_priorities.append(_first_order_backward_beat_priorities(meter_stratum))
    # we reverse the strata here, because the position in the lowest level stratum matters the most
    strata_backward_beat_priorities.reverse()

    strata_lengths = [len(x) for x in strata_backward_beat_priorities]

    strata_multipliers = [1]
    last_multiplier = 1
    for l in strata_lengths[:-1]:
        last_multiplier *= l
        strata_multipliers.append(last_multiplier)

    overall_beat_priorities = []
    for combination in itertools.product(*strata_backward_beat_priorities):
        overall_beat_priorities.append(sum(p*q for p, q in zip(combination, strata_multipliers)))

    return overall_beat_priorities


INT_OR_FLOAT = TypeVar("IntOrFloat", int, float)


def get_indispensability_array(rhythmic_strata: Sequence[Union[Tuple, int]],
                               normalize: bool = False) -> Sequence[INT_OR_FLOAT]:
    """
    A slightly more general approach to indispensability than the one proposed by Barlow. In this version, each
    rhythmic layer can be a tuple representing an additive grouping. Thus a 3+2+3 layer would be represented by
    (3, 2, 3). Rhythmic layers can also simply be numbers, in which case their indispensabilities are treated
    as increasing monotonically towards the downbeat.

    :param rhythmic_strata: List of tuples representing rhythmic strata, or simple numbers
    :param normalize: if True, scale indispensabilities to go from 0 to 1
    :return: a list of ints or floats representing the indispensabilities or normalized indispensabilities, respectively
    """
    backward_beat_priorities = _get_backward_beat_priorities(*rhythmic_strata)
    length = len(backward_beat_priorities)
    backward_indispensability_array = [length-1-backward_beat_priorities.index(i) for i in range(length)]
    indispensability_array = _rotate(backward_indispensability_array, 1)
    indispensability_array.reverse()
    if normalize:
        max_val = max(indispensability_array)
        return [float(x)/max_val for x in indispensability_array]
    else:
        return indispensability_array


def _standardize_strata(rhythmic_strata: Sequence[int]) -> Sequence[Union[Tuple, int]]:
    strata = []
    for stratum in rhythmic_strata:
        assert isinstance(stratum, int) and stratum > 0
        if stratum > 2:
            strata.append(_decompose_to_twos_and_threes(stratum))
        else:
            strata.append(stratum)
    return strata


def get_standard_indispensability_array(rhythmic_strata: Sequence[int],
                                        normalize: bool = False) -> Sequence[INT_OR_FLOAT]:
    """
    Returns a list of the indispensabilities of different pulses in a meter defined by the rhythmic_strata.
    (See Barlow's "On Musiquantics", http://clarlow.org/wp-content/uploads/2016/10/On-MusiquanticsA4.pdf)

    :param rhythmic_strata: a tuple representing the rhythmic groupings from large scale to small scale. For instance,
        the sixteenth-note pulses in a measure of 9/8 would be represented by (3, 3, 2), since there are three beats of
        three eighth notes, each of which has two sixteenth notes.
    :param normalize: if True, scale all indispensabilities to the range 0 to 1
    :return: a list of integer indispensabilities, or float if normalize is set to true
    """
    return get_indispensability_array(_standardize_strata(rhythmic_strata), normalize)


# -------------------------------------------- Metric Coherence -----------------------------------------------


def _get_num_pulses_in_meter(rhythmic_strata):
    # convenience method for calculating num pulses from rhythmic strata (need to deal with lists within
    # the list, in the case of any additive meters)
    def sum_list_or_number(x): sum(x) if hasattr(x, "__len__") else x
    return reduce(lambda x, y: sum_list_or_number(x) * sum_list_or_number(y), rhythmic_strata)


def _get_subdivided_strata(rhythmic_strata_1, bar_tempo_1, rhythmic_strata_2, bar_tempo_2):
    # this function gets the two meters to the same shared fundamental pulse
    pulses_in_meter_1 = _get_num_pulses_in_meter(rhythmic_strata_1)
    pulses_in_meter_2 = _get_num_pulses_in_meter(rhythmic_strata_2)
    smallest_pulse_tempo_1 = pulses_in_meter_1 * bar_tempo_1
    smallest_pulse_tempo_2 = pulses_in_meter_2 * bar_tempo_2
    shared_tempo = _lcm(smallest_pulse_tempo_1, smallest_pulse_tempo_2)
    subdivided_strata_1 = list(rhythmic_strata_1) + sorted(_prime_factor(shared_tempo / smallest_pulse_tempo_1),
                                                           reverse=True)
    subdivided_strata_2 = list(rhythmic_strata_2) + sorted(_prime_factor(shared_tempo / smallest_pulse_tempo_2),
                                                           reverse=True)
    return subdivided_strata_1, subdivided_strata_2


def _get_comparable_indispensability_arrays(subdivided_strata_1, subdivided_strata_2, standard_barlow=True):
    indispensabilities_1 = get_standard_indispensability_array(subdivided_strata_1, normalize=True) if standard_barlow \
        else get_indispensability_array(subdivided_strata_1, normalize=True)
    indispensabilities_2 = get_standard_indispensability_array(subdivided_strata_2, normalize=True) if standard_barlow \
        else get_indispensability_array(subdivided_strata_2, normalize=True)
    joint_pattern_length = _lcm(len(indispensabilities_1), len(indispensabilities_2))
    return indispensabilities_1 * (joint_pattern_length / len(indispensabilities_1)), \
           indispensabilities_2 * (joint_pattern_length / len(indispensabilities_2))


def calculate_metric_coherence(rhythmic_strata_1: Sequence[Union[Tuple, int]], bar_tempo_1: float,
                               rhythmic_strata_2: Sequence[Union[Tuple, int]], bar_tempo_2: float,
                               standard_barlow: bool = True) -> float:
    """
    Calculates the "metric coherence" of two meters, as described on pages 46-47 of Barlow's "On Musiquantics".
    Essentially this is a (square) correlation between the indispensabilities of the two meters when they are placed
    side-by-side. Often this will require first subdiving one or both of the meters further so that they share a
    common basic pulse.

    :param rhythmic_strata_1: Metric strata defining the first meter, of the exact same type that would be passed to
        :func:`get_indispensability_array` or to :func:`get_standard_indispensability_array`. (Which of these
        functions it gets passed to depends on the `standard_barlow` argument.
    :param bar_tempo_1: Number of complete cycles of the first meter per minute.
    :param rhythmic_strata_2: Metric strata defining the second meter.
    :param bar_tempo_2: Number of complete cycles of the second meter per minute.
    :param standard_barlow: Whether or not to interpret the rhythmic strata using the standard Barlow version of
        indispensability, or my slightly broader version that allows additive layers.
    :return: the coherence of the two meters as a float between 0 and 1
    """
    subdivided_strata_1, subdivided_strata_2 = _get_subdivided_strata(rhythmic_strata_1, bar_tempo_1, 
                                                                      rhythmic_strata_2, bar_tempo_2)
    indisp_array_1, indisp_array_2 = _get_comparable_indispensability_arrays(subdivided_strata_1,
                                                                             subdivided_strata_2, standard_barlow)
    multiplied_squares = [(x * y) ** 2 for x, y in zip(indisp_array_1, indisp_array_2)]
    average_product_squared = sum(multiplied_squares) / len(multiplied_squares)
    # return the mysteriously scaled value (this has to do with getting the output to lie between 0 and 1)
    return -1/(2*math.log((9*average_product_squared - 1) / 3.5))


def calculate_metric_similarity(rhythmic_strata_away: Sequence[Union[Tuple, int]], bar_tempo_away: float,
                                rhythmic_strata_home: Sequence[Union[Tuple, int]], bar_tempo_home: float,
                                standard_barlow: bool = True):
    """
    As Barlow explains on page 46 of "On Musiquantics," the metric coherece of a meter with itself is not always 1.
    This is because metric coherence conflates a measurement of the similarity of two meters with a measurement of the
    complexity of each of these meters. Metric similarity compensates for this by comparing a "home" meter with an
    "away" meter, and dividing the coherence of the two meters by the auto_coherence of the first meter with itself.
    With this scaling, the metric similarity of a meter with itself is always 1. (Note that this is not commutative
    the similarity of A to B is not the same as the similarity of B to A. This is why we distinguish a home from an
    away meter.)

    :param rhythmic_strata_away: see :func:`calculate_metric_coherence`.
    :param bar_tempo_away: see :func:`calculate_metric_coherence`.
    :param rhythmic_strata_home: see :func:`calculate_metric_coherence`.
    :param bar_tempo_home: see :func:`calculate_metric_coherence`.
    :param standard_barlow: see :func:`calculate_metric_coherence`.
    :return: the similarity of the two meters as a float between 0 and 1
    """
    # measure of how close the "away" meter is to the "home" meter. It's directional like that (often).
    auto_coherence = calculate_metric_coherence(rhythmic_strata_home, bar_tempo_home, 
                                                rhythmic_strata_home, bar_tempo_home, standard_barlow)
    cross_coherence = calculate_metric_coherence(rhythmic_strata_away, bar_tempo_away, 
                                                 rhythmic_strata_home, bar_tempo_home, standard_barlow)
    return cross_coherence / auto_coherence
