__author__ = 'mpevans'

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
from collections.abc import Sequence
from itertools import chain, count

# ---------------------------------------------- Utility Functions -------------------------------------------------


# decorator that saves function output
def save_answers(func):
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


def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)


def is_prime(a):
    return not (a < 2 or any(a % x == 0 for x in range(2, int(a ** 0.5) + 1)))


def prime_factor(n):
    i = 2
    primes = []
    while i * i <= n:
        while n % i == 0:
            n /= i
            primes.append(i)
        i += 1

    if n != 1:
        primes.append(n)

    return primes


def rotate(l, n):
    return l[n:] + l[:n]


def get_nth_prime(n):
    # counting 2 as the 0th prime
    if n == 0:
        return 2

    if hasattr(get_nth_prime, "primes"):
        assert isinstance(get_nth_prime.primes, list)
        if n < len(get_nth_prime.primes):
            return get_nth_prime.primes[n]
        else:
            k = get_nth_prime.primes[len(get_nth_prime.primes) - 1] + 1
    else:
        get_nth_prime.primes = [2]
        k = 3

    while len(get_nth_prime.primes) <= n:
        # get the next prime
        found_a_prime = True
        for prime in get_nth_prime.primes:
            if k % prime == 0:
                found_a_prime = False
                break
        if found_a_prime:
            get_nth_prime.primes.append(k)
        else:
            k += 1

    return k


def gaussian_discount(x, center, standard_deviation):
    return math.exp(-(x-center)**2/(2*standard_deviation**2))


# ---------------------------------------- Indigestibility and Harmonicity ------------------------------------------


def indigestibility(n):
    assert isinstance(n, int) and n > 0
    if is_prime(n):
        return 2 * float((n-1)**2) / n
    else:
        total = 0
        for factor in prime_factor(n):
            total += indigestibility(factor)
        return total


def harmonicity(p, q):
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

# [(4, 3), (75, 56), (27, 20), (675, 512), (320, 243), (21, 16), (256, 189), (49, 36), (72, 55), (15, 11), (64, 49), (512, 375)]
# [(4, 3), (75, 56), (27, 20), (675, 512), (320, 243), (21, 16), (256, 189), (49, 36), (72, 55), (15, 11), (64, 49), (512, 375)]

# This is quicker because it first narrows down the possibilities for higher primes
# I think it could be made still quicker by splitting it up still more
# basically we are pitting the efficiency of itertools.product with the efficiency of checking fewer possibilities
# but using more python code
@save_answers
def _get_candidate_prime_pool(min_harmonicity, high_low_cutoff=0.25):
    max_inharmonicity = 1.0 / min_harmonicity
    max_primes = []
    n = 0

    while indigestibility(get_nth_prime(n)) < max_inharmonicity:
        # old system
        max_primes.append(_get_max_prime_power(get_nth_prime(n), min_harmonicity))
        n += 1

    first_high_prime = int(len(max_primes)*high_low_cutoff)
    low_ranges = [range(0, x+1) for x in max_primes[:first_high_prime]]
    high_ranges = [range(0, x+1) for x in max_primes[first_high_prime:]]

    acceptable_high_prime_combos = []
    for primes in itertools.product(*high_ranges):
        val = 0
        for i, power in enumerate(primes):
            val += indigestibility(get_nth_prime(i+ first_high_prime)) * power
        if val < max_inharmonicity:
            acceptable_high_prime_combos.append(primes)

    acceptable_prime_combos = []
    for high_primes, low_primes in itertools.product(acceptable_high_prime_combos, itertools.product(*low_ranges)):
        primes = low_primes + high_primes
        val = 0
        for i, power in enumerate(primes):
            val += indigestibility(get_nth_prime(i)) * power
        if val < max_inharmonicity:
            acceptable_prime_combos.append(primes)
    return acceptable_prime_combos


# generates all possible ratios within a cent range that satisfy a minimum harmonicity
def generate_ratio_candidates(cent_range, min_harmonicity):
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
                    top *= get_nth_prime(i) ** power
                else:
                    bottom *= get_nth_prime(i) ** power
            if interval_lower_bound < float(top)/bottom < interval_upper_bound:
                ratio_candidates.append((top, bottom))
    return set(ratio_candidates)


# nominal tolerance applies a gaussian envelope whereby ratios that are the nominal tolerance away are discounted 95%
# this happens at 2.447 * the standard deviation, so standard dev = nominal_tolerance / 2.447
# also we'll only generate possibilities within the nominal tolerance, since more than 95% overwhelming
def get_ratio_candidates(desired_cent_ratio, nominal_tolerance, min_harmonicity, num_candidates=None):
    ratio_candidates = generate_ratio_candidates((desired_cent_ratio - nominal_tolerance,
                                                  desired_cent_ratio + nominal_tolerance), min_harmonicity)
    candidates_and_values = []
    for ratio in ratio_candidates:
        cent_ratio = math.log(float(ratio[0])/ratio[1])/math.log(2) * 1200
        discount = gaussian_discount(cent_ratio, desired_cent_ratio, nominal_tolerance / 2.447)
        candidates_and_values.append((ratio, math.fabs(harmonicity(*ratio)) * discount))
    candidates_and_values.sort(key=lambda x : x[1], reverse=True)
    return [cv[0] for cv in candidates_and_values] if num_candidates is None else \
        [cv[0] for cv in candidates_and_values[:num_candidates]]


def get_tuning_inharmonicity(the_tuning):
    total_inharmonicity = 0
    for interval in itertools.combinations(the_tuning, 2):
        # interval is something like ((27, 16), (15, 8))
        # what we want is to look at the absolute harmonicity of (15*16) / (27*8)
        # the Fraction class reduces it for us, probably pretty efficiently
        reduced_fraction = Fraction(interval[0][1]*interval[1][0], interval[0][0]*interval[1][1])
        total_inharmonicity += indigestibility(reduced_fraction.numerator) + \
                              indigestibility(reduced_fraction.denominator)
    return total_inharmonicity


def rationalize_scale(cents_values, nominal_tolerance, min_harmonicity, num_candidates, num_to_return=None, write_pretty=False):
    """
    :param cents_values: An array of cent values for the pitches of the scale, all in reference to a distance from
    the first degree of the scale
    :param nominal_tolerance: Nominal tolerance used in generating interval candidates
    :param min_harmonicity: Minimum harmonicity used in generating interval candidates
    :param num_candidates: Number of alternative candidates considered for each interval
    :param num_to_return: if None, we just return the best tuning (or a list of equally best tunings) and the
        specific harmonicity. If a number n, we return a list of the top n tunings as ordered pairs (tuning, harmonicity)
    :param write_pretty: if True, it returns a list fraction strings (easier to read); if false, a list of tuples
    """
    candidates = []
    print("Generating Candidates...")
    for i, cent_value in enumerate(cents_values):
        print("  ...for scale degree", i+1)
        candidates.append(get_ratio_candidates(cent_value, nominal_tolerance, min_harmonicity, num_candidates))

    number_of_tunings = reduce(lambda a, b: a*b, map(len, candidates))
    if number_of_tunings == 0:
        raise Exception("No available candidates for some scale degrees")
    else:
        print("Comparing all", number_of_tunings, "possible tunings...")
    # keeps a list of the best tunings (as long as the num_to_return)
    # each entry goes (tuning, inharmonicity) if num_to_return = n >= 1
    # otherwise, if num_to_return is None, we just keep a list of the best tunings, each having least_tuning_inharmonicity
    best_tunings = []
    # only used if we are just returning the best tuning(s)
    least_tuning_inharmonicity = float("inf")
    tunings_checked = 0
    for tuning_choice in itertools.product(*candidates):
        tuning_inharmonicity = get_tuning_inharmonicity(tuning_choice)
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
# print rationalize_scale([0, 200, 400, 500, 700, 900, 1100, 1200], 40, 0.03, 3)
# HARMONIC MINOR SCALE
# print rationalize_scale([0, 200, 300, 500, 700, 800, 1100, 1200], 40, 0.03, 3)
# PENTATONIC SCALE
# print rationalize_scale([0, 200, 400, 700, 900, 1200], 40, 0.03, 3)
# WHOLE-TONE SCALE
# print rationalize_scale([0, 200, 400, 600, 800, 1000, 1200], 40, 0.03, 3)
# NOTE: Fascinatingly, for the whole tone scale, there there are two identical best tunings with the exact same
# specific harmonicity. There's the one listed in the book (1/1, 10/9, 5/4, 64/45, 8/5, 16/9, 2/1), but there's
# also (1/1, 9/8, 5/4, 45/32, 8/5, 9/5, 2/1)
# BOHLEN-PIERCE #1
# print rationalize_scale([0, 146, 293, 439, 585, 732, 878, 1024, 1170, 1317, 1463, 1609, 1756, 1902], 40, 0.04, 2)
# BOHLEN-PIERCE #2
# print rationalize_scale([0, 146, 293, 439, 585, 732, 878, 1024, 1170, 1317, 1463, 1609, 1756, 1902], 20, 0.05, 2)
# CHROMATIC
# print rationalize_scale([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200], 30, 0.04, 2, 4)
# Note that there are some discrepancies here: one of the reasons is that (probably due to rounding) I get
#    different candidates for the 10th scale degree and 9/5 is the third, and therefore doesn't make the cut
# print get_ratio_candidates(1000, 30, 0.04, 5)
# # COMPARE: my program's ideal tuning, the tuning from Musiquantics, the tuning from Musiquantics with 16/9 substituted for 9/5
# print get_tuning_inharmonicity(((1, 1), (16, 15), (10, 9), (6, 5), (5, 4), (4, 3), (64, 45), (3, 2), (8, 5), (5, 3), (16, 9), (15, 8), (2, 1))), \
#     get_tuning_inharmonicity(((1, 1), (16, 15), (9, 8), (6, 5), (5, 4), (4, 3), (45, 32), (3, 2), (8, 5), (5, 3), (9, 5), (15, 8), (2, 1))), \
#     get_tuning_inharmonicity(((1, 1), (16, 15), (9, 8), (6, 5), (5, 4), (4, 3), (45, 32), (3, 2), (8, 5), (5, 3), (16, 9), (15, 8), (2, 1)))
# Fascinatingly, my tuning and the tuning from Musiquantics have identical Specific Harmonicities!
# But if you take the Musiquantics tuning and substitute 16/9 it doesn't like it. (Doesn't really fit with the scale.)
# ALSO: if we use Nominal tolerance 40, the 9/5 is included and we get it as well
# print rationalize_scale([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200], 40, 0.04, 2)

# ---------------------------------------------- Indispensability -----------------------------------------------


def decompose_to_twos_and_threes(n):
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


class NestedBeatList:

    def __init__(self, nested_list: list):
        self.contents = nested_list
        for i, x in enumerate(self.contents):
            if isinstance(x, list):
                self.contents[i] = NestedBeatList(x)
        if not any(isinstance(x, NestedBeatList) for x in self.contents):
            self.total_count = len(self.contents)
        else:
            self.total_count = sum(x.total_count if isinstance(x, NestedBeatList) else 1 for x in self.contents)

    def remove_redundant_depth(self):
        if all(hasattr(x, "__len__") and len(x) == 1 for x in self.contents):
            self.contents = [x.contents[0] for x in self.contents]
        for x in self.contents:
            if isinstance(x, NestedBeatList):
                x.remove_redundant_depth()

    def iterate_and_consume(self):
        # if it's just a flat list,
        if not any(isinstance(x, NestedBeatList) for x in self.contents):
            while len(self.contents) > 0:
                self.total_count -= 1
                yield self.contents.pop(0)
            return

        sub_list_iterators = [x.iterate_and_consume() for x in self.contents]
        # take one from each group
        for sub_list_iterator in sub_list_iterators:
            self.total_count -= 1
            yield next(sub_list_iterator)

        while self.total_count > 0:
            self.remove_redundant_depth()
            print(self)
            if not any(isinstance(x, NestedBeatList) for x in self.contents):
                while len(self.contents) > 0:
                    self.total_count -= 1
                    yield self.contents.pop(0)
                return

            # first check to see if there's any unevenness to be ironed out,
            # and if so, take note of the (first) one with the biggest unevenness surplus
            most_uneven_sublist_iterator = None
            biggest_surplus = 0
            for sublist, sub_list_iterator in zip(self.contents, sub_list_iterators):
                if isinstance(sublist, NestedBeatList):
                    surplus = sublist.unevenness_surplus()
                    if surplus > biggest_surplus:
                        most_uneven_sublist_iterator = sub_list_iterator
                        biggest_surplus = surplus

            if most_uneven_sublist_iterator is not None:
                self.total_count -= 1
                yield next(most_uneven_sublist_iterator)
            else:
                biggest_count = max(sublist.total_count if isinstance(sublist, NestedBeatList) else 1
                                    for sublist in self.contents)
                for sublist, sub_list_iterator in zip(self.contents, sub_list_iterators):
                    this_count = sublist.total_count if isinstance(sublist, NestedBeatList) else 1
                    if this_count == biggest_count:
                        self.total_count -= 1
                        yield next(sub_list_iterator)
                        break

    def to_nested_list(self):
        if not any(isinstance(x, NestedBeatList) for x in self.contents):
            return self.contents
        else:
            return [(x.to_nested_list() if isinstance(x, NestedBeatList) else x) for x in self.contents]

    # def is_even(self):
    #     # for the NestedBeatList to be considered "even", it must have elements of all the same length
    #     # and if those elements are nested beat lists, they must also be even
    #     contents_lengths = [len(x) if hasattr(x, "__len__") else 1 for x in self.contents]
    #     return all(x == contents_lengths[0] for x in contents_lengths) and \
    #            all(x.is_even() if isinstance(x, NestedBeatList) else True for x in self.contents)

    def unevenness_surplus(self):
        if not any(isinstance(x, NestedBeatList) for x in self.contents):
            return 0
        min_size_of_sublist = min(x.total_count if isinstance(x, NestedBeatList) else 1 for x in self.contents)
        return sum(x.total_count - min_size_of_sublist for x in self.contents)

    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return "NestedBeatList({})".format(self.to_nested_list())


class MetricLayer:

    def __init__(self, *groups, break_up_large_groups=False):
        """
        A single metric layer formed by the additive concatenation of the given groups. These groups can themselves
        be metric layers, which allows for nested additive structures.

        :param groups: list of additively combined groups. If all integers, then this is like a simple additive meter
            without considering subdivisions. For instance, (2, 4, 3) is like the time signature (2+4+3)/8. However,
            any component of this layer can instead be itself a MetricLayer, allowing for nesting.
        Each one can either be a number or a Metric layer
        """
        assert all(isinstance(x, (int, MetricLayer))for x in groups), \
            "Metric layer groups must either be integers or metric groups themselves"

        self.groups = list(groups)

        if break_up_large_groups:
            self.break_up_large_groups()

        self._remove_redundant_nesting()

    @classmethod
    def from_string(cls, input_string: str, break_up_large_groups=False):
        import re
        input_string = input_string.replace(" ", "")
        out = eval(re.sub(r'(^|[^*])(\d)', r"\1MetricLayer(\2)", input_string))
        if break_up_large_groups:
            out.break_up_large_groups()
        return out

    def break_up_large_groups(self):
        for i, group in enumerate(self.groups):
            if isinstance(group, int):
                if group > 3:
                    self.groups[i] = MetricLayer(*decompose_to_twos_and_threes(group))
            else:
                self.groups[i].break_up_large_groups()
        return self

    def _remove_redundant_nesting(self):
        """
        Since MetricLayer(MetricLayer(*)) = MetricLayer(*), this method removes those unnecessary nestings.
        """
        if len(self.groups) == 1 and isinstance(self.groups[0], MetricLayer):
            self.groups = self.groups[0].groups
            self._remove_redundant_nesting()
        else:
            for i, group in enumerate(self.groups):
                if isinstance(group, MetricLayer):
                    group._remove_redundant_nesting()
                    if len(group.groups) == 1 and isinstance(group.groups[0], int):
                        self.groups[i] = group.groups[0]
        return self

    @staticmethod
    def _count_nested_list(l):
        return sum(MetricLayer._count_nested_list(x) if hasattr(x, "__len__") else 1 for x in l)

    @staticmethod
    def _increment_nested_list(l, increment):
        for i, element in enumerate(l):
            if isinstance(element, list):
                MetricLayer._increment_nested_list(element, increment)
            else:
                l[i] += increment
        return l

    @staticmethod
    def _iterate_beat_priorities_and_remaining_length(l):
        if not any(hasattr(x, "__len__") for x in l):
            while len(l) > 0:
                yield l.pop(0), len(l)
            return

        group_lengths = [len(x) for x in l]

        group_iterators = [MetricLayer._iterate_beat_priorities_and_remaining_length(x) for x in l]

        # get one from every layer first
        for i in range(len(l)):
            next_value, new_group_length = next(group_iterators[i])
            group_lengths[i] = new_group_length
            yield next_value, sum(group_length > 0 for group_length in group_lengths)

        # then continually take one from the next
        while sum(group_length > 0 for group_length in group_lengths) > 0:
            max_length = max(group_lengths)
            for i in range(len(l)):
                if group_lengths[i] == max_length:
                    next_value, new_group_length = next(group_iterators[i])
                    group_lengths[i] = new_group_length
                    yield next_value, sum(group_length > 0 for group_length in group_lengths)
                    break

    def iterate_backward_beat_priorities(self):
        return (x for x, length in
                MetricLayer._iterate_beat_priorities_and_remaining_length(self.get_nested_beat_groups()))

    def get_nested_beat_groups(self):
        beat_groups = []
        beat = 0
        for group in reversed(self.groups):
            beat_group = list(range(group)) if isinstance(group, int) else group.get_nested_beat_groups()
            MetricLayer._increment_nested_list(beat_group, beat)
            beat += MetricLayer._count_nested_list(beat_group)
            beat_groups.append(beat_group)
        return beat_groups

    def get_backward_beat_priorities(self):
        nested_beat_list = NestedBeatList(self.get_nested_beat_groups())
        return list(nested_beat_list.iterate_and_consume())

    # def get_backward_beat_priorities(self):
    #     """
    #     Returns the order of beats from most indispensable to least indispensable. "Backward" refers to the fact that
    #     they are counted backwards from the downbeat, which turns out to be the easier way to work with
    #     indispensability. So for instance, when we say the backward beat priorities are (0, 2, 1, 3), we are referring
    #     to the positions in the bar like this: [0, 3, 2, 1] (downbeat first, then count from the end backwards).
    #     So (0, 2, 1, 3) refers to the following metric positions:
    #         [*, _, _, _] = 0
    #         [_, _, *, _] = 2
    #         [_, _, _, *] = 1
    #         [_, *, _, _] = 3
    #     Leading to the indispensability array: [3, 0, 2, 1]
    #     """
    #
    #     if len(self.groups) > 1 or isinstance(self.groups[0], MetricLayer):
    #         # first reverse the group lengths, since we are doing everything backwards
    #         # lets take the example of groups = (3, 5, 2)
    #         group_lengths = self.groups[::-1]
    #         # now group_lengths = (2, 5, 3), since we calculate backwards
    #
    #         # then construct beat groups according to their (backwards) position in the bar
    #         beat_groups = []
    #         beat = 0
    #         for group in group_lengths:
    #             if not isinstance(group, MetricLayer):
    #                 group = MetricLayer(group)
    #
    #             beat_group = [x + beat for x in group.get_backward_beat_priorities()]
    #             beat += len(beat_group)
    #             beat_groups.append(beat_group)
    #             # beat_group = []
    #             # for i in range(group):
    #             #     beat_group.append(beat)
    #             #     beat += 1
    #             # beat_groups.append(beat_group)
    #         # in our example, this results in beat_groups = [[0, 1], [2, 3, 4, 5, 6], [7, 8, 9]]
    #         print(beat_groups)
    #         # OK, now we move the beats to a list in order from most indispensable to least
    #         order_of_indispensability = []
    #
    #         # first take the first of each group (these are the beats)
    #         for beat_group in beat_groups:
    #             order_of_indispensability.append(beat_group.pop(0))
    #         # example: order_of_indispensability = [0, 2, 7]
    #
    #         # then gradually pick all the beats
    #         # beat groups that are the longest get whittled away first, until they
    #         # are no longer than any of the others. Always we go in order (backwards through the bar)
    #         # example: 3, 4, 5 get added next (remember, it's backwards, so we're adding the pulses
    #         #   leading up to the beat following the 5 group) once there are equally many pulses left
    #         #   in each beat, we add from each group in order (i.e. backwards order).
    #         largest_beat_group_length = max([len(x) for x in beat_groups])
    #         while largest_beat_group_length > 0:
    #             for beat_group in beat_groups:
    #                 if len(beat_group) == largest_beat_group_length:
    #                     order_of_indispensability.append(beat_group.pop(0))
    #             largest_beat_group_length = max([len(x) for x in beat_groups])
    #
    #         return order_of_indispensability
    #     else:
    #         # backward beat priorities of [0, 1, 2, 3] results in indispensability [3, 0, 1, 2]
    #         return range(self.groups[0])

    @staticmethod
    def indispensability_array_from_string(initialization_string, break_up_large_groups=False):
        return MetricLayer.from_string(
            initialization_string, break_up_large_groups=break_up_large_groups).get_indispensability_array()

    def get_indispensability_array(self):
        """
        Return the indispensability array, flattening out sub-layers

        :return: an indispensability array
        """
        backward_beat_priorities = list(self.get_backward_beat_priorities())
        length = len(backward_beat_priorities)
        backward_indispensability_array = [length - 1 - backward_beat_priorities.index(i) for i in range(length)]
        indispensability_array = rotate(backward_indispensability_array, 1)
        indispensability_array.reverse()
        return indispensability_array

    def extend(self, other_metric_layer, in_place=True):
        """
        Extend this layer by appending the groups of another metric layer
        """
        if in_place:
            self.groups.extend(other_metric_layer.groups)
            return self._remove_redundant_nesting()
        else:
            return MetricLayer(*self.groups, *other_metric_layer.groups)

    def append(self, other_metric_layer, in_place=True):
        if in_place:
            self.groups.append(other_metric_layer)
            return self._remove_redundant_nesting()
        else:
            return MetricLayer(*self.groups, other_metric_layer)

    def join(self, other_metric_layer):
        return MetricLayer(self, other_metric_layer)

    def __add__(self, other):
        assert isinstance(other, (MetricLayer, int))
        if isinstance(other, MetricLayer) and len(other.groups) > 1:
            return self.join(other)
        else:
            return self.append(other, in_place=False)

    def __mul__(self, other):
        assert isinstance(other, (MetricLayer, int))
        if isinstance(other, int):
            return MetricLayer(*([self] * other))
        else:
            return MetricLayer(*(self * group for group in other.groups))

    def __radd__(self, other):
        assert isinstance(other, (MetricLayer, int))
        if other == 0:
            # This allows the "sum" command in __mul__ above to work
            return self
        elif isinstance(other, int):
            return MetricLayer(other) + self
        else:
            return other + self

    def __repr__(self):
        return "MetricLayer({})".format(", ".join(str(x) for x in self.groups))


#  https://stackoverflow.com/questions/6039103/counting-depth-or-the-deepest-level-a-nested-list-goes-to (pillmuncher)
def depth(seq):
    if not isinstance(seq, Sequence):
        return 0
    seq = iter(seq)
    try:
        for level in count():
            seq = chain([next(seq)], seq)
            seq = chain.from_iterable(s for s in seq if isinstance(s, Sequence))
    except StopIteration:
        return level


def flatten_beat_groups(beat_groups):
    out = []
    # first big beats
    for sub_group in beat_groups:
        out.append(sub_group.pop(0))
    # then the pickups to those beats
    for sub_group in beat_groups:
        if len(sub_group) > 0:
            out.append(sub_group.pop(0))
    # then by the longest chain, and secondarily by order (big beat indispensability)
    while True:
        max_subgroup_length = max(len(sub_group) for sub_group in beat_groups)
        if max_subgroup_length == 0:
            break
        else:
            for sub_group in beat_groups:
                if len(sub_group) == max_subgroup_length:
                    out.append(sub_group.pop(0))
                    break
    return out


def normalize_depth(l):
    # If some branches of the beat priorities tree don't go as far as others, we should embed
    # them further so that every beat is at the same depth within the tree
    max_depth = max(depth(element) for element in l)
    for i in range(len(l)):
        while depth(l[i]) < max_depth:
            l[i] = [l[i]]
    for element in l:
        if isinstance(element, list):
            normalize_depth(element)
    return l





bob = MetricLayer.from_string("2 * (3 + 2 + 2)")
print(bob.get_nested_beat_groups())
flatten_it(bob.get_nested_beat_groups())

frank = MetricLayer.from_string("(3 + 2) + (2+2+3) + 3")
print(frank)
print("F1", frank.get_nested_beat_groups())
print("F2", normalize_depth(frank.get_nested_beat_groups()))
flatten_it(flatten_it([[[0, 1, 2]], [[3, 4, 5], [6, 7], [8, 9]], [[10, 11], [12, 13, 14]]]))

exit()


# TODO: Try having beat_groups use indispensability strata
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
        # example: order_of_indispensibility = [0, 2, 7]

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


def get_indispensability_array(rhythmic_strata, normalize=False):
    backward_beat_priorities = _get_backward_beat_priorities(*rhythmic_strata)
    print(backward_beat_priorities)
    length = len(backward_beat_priorities)
    backward_indispensability_array = [length-1-backward_beat_priorities.index(i) for i in range(length)]
    indispensability_array = rotate(backward_indispensability_array, 1)
    indispensability_array.reverse()
    if normalize:
        max_val = max(indispensability_array)
        return [float(x)/max_val for x in indispensability_array]
    else:
        return indispensability_array


def standardize_strata(rhythmic_strata):
    strata = []
    for stratum in rhythmic_strata:
        assert isinstance(stratum, int) and stratum > 0
        if stratum > 2:
            strata.append(decompose_to_twos_and_threes(stratum))
        else:
            strata.append(stratum)
    return strata


def get_standard_indispensability_array(rhythmic_strata, normalize=False):
    return get_indispensability_array(standardize_strata(rhythmic_strata), normalize)


# print(MetricLayer.indispensability_array_from_string("4 + (2 + 2)"))
# print(get_indispensability_array(((2, 3), 3, 2, (2, 2, 3))))
# print(MetricLayer.indispensability_array_from_string("(2 +2 +3)*2*3*(2+3)"))
# exit()
#
# print(MetricLayer(MetricLayer(2, 2), MetricLayer(2, 2), MetricLayer(2, 2, 2)).get_indispensability_array())
# exit()
# print(get_indispensability_array(((2, 3), 2)))
# print(MetricLayer.from_string("2 * (2 + 3)"))
# print("here")

# print(get_indispensability_array(((2, 3), 2)))
# MetricLayer.from_string("2 * (2 + 3)").get_backward_beat_priorities()
# MetricLayer.from_string("4 + (2 + 2)").get_backward_beat_priorities()



# frank = NestedBeatList(MetricLayer.from_string("2 * 2 * (2 + 3)").get_nested_beat_groups())
# print(frank)
# print(list(frank.iterate_and_consume()))
# print("frank", frank)
# print(frank.total_count)
#
# print("----")
# bob = NestedBeatList([[[0, 1], [2, 3]], [4, 5, 6, 7]])
# print(bob)
# print(list(bob.iterate_and_consume()))
# print("bob", bob)



print(MetricLayer.indispensability_array_from_string("2 * (2 + 3)"))
print(get_indispensability_array(((3, 2, 2), 2)))
print(MetricLayer.from_string("2 * (3 + 2 + 2)"))
exit()

# -------------------------------------------- Metric Coherence -----------------------------------------------


def _get_num_pulses_in_meter(rhythmic_strata):
    # convenience method for calculating num pulses from rhythmic strata (need to deal with lists within
    # the list, in the case of any additive meters)
    def sum_list_or_number(x): sum(x) if hasattr(x, "__len__") else x
    return reduce(lambda x, y: sum_list_or_number(x) * sum_list_or_number(y), rhythmic_strata)


def _get_subdivided_stata(rhythmic_strata_1, bar_tempo_1, rhythmic_strata_2, bar_tempo_2):
    # this function gets the two meters to the same shared fundamental pulse
    pulses_in_meter_1 = _get_num_pulses_in_meter(rhythmic_strata_1)
    pulses_in_meter_2 = _get_num_pulses_in_meter(rhythmic_strata_2)
    smallest_pulse_tempo_1 = pulses_in_meter_1 * bar_tempo_1
    smallest_pulse_tempo_2 = pulses_in_meter_2 * bar_tempo_2
    shared_tempo = lcm(smallest_pulse_tempo_1, smallest_pulse_tempo_2)
    subdivided_strata_1 = list(rhythmic_strata_1) + sorted(prime_factor(shared_tempo/smallest_pulse_tempo_1), reverse=True)
    subdivided_strata_2 = list(rhythmic_strata_2) + sorted(prime_factor(shared_tempo/smallest_pulse_tempo_2), reverse=True)
    return subdivided_strata_1, subdivided_strata_2


def _get_comparable_indespensibility_arrays(subdivided_strata_1, subdivided_strata_2, standard_barlow=True):
    indispensibilities_1 = get_standard_indispensability_array(subdivided_strata_1, normalize=True) if standard_barlow \
        else get_indispensability_array(subdivided_strata_1, normalize=True)
    indispensibilities_2 = get_standard_indispensability_array(subdivided_strata_2, normalize=True) if standard_barlow \
        else get_indispensability_array(subdivided_strata_2, normalize=True)
    joint_pattern_length = lcm(len(indispensibilities_1), len(indispensibilities_2))
    return indispensibilities_1 * (joint_pattern_length / len(indispensibilities_1)), \
           indispensibilities_2 * (joint_pattern_length / len(indispensibilities_2))


def calculate_metric_coherence(rhythmic_strata_1, bar_tempo_1, rhythmic_strata_2, bar_tempo_2, standard_barlow=True):
    subdivided_strata_1, subdivided_strata_2 = _get_subdivided_strata(rhythmic_strata_1, bar_tempo_1, rhythmic_strata_2, bar_tempo_2)
    indisp_array_1, indisp_array_2 = _get_comparable_indespensibility_arrays(subdivided_strata_1, subdivided_strata_2, standard_barlow)
    multiplied_squares = [(x * y) ** 2 for x, y in zip(indisp_array_1, indisp_array_2)]
    average_product_squared = sum(multiplied_squares) / len(multiplied_squares)
    # return the mysteriously scaled value
    return -1/(2*math.log((9*average_product_squared - 1) / 3.5))


def calculate_metric_similarity(rhythmic_strata_away, bar_tempo_away, rhythmic_strata_home, bar_tempo_home, standard_barlow=True):
    # measure of how close the "away" meter is to the "home" meter. It's directional like that (often).
    auto_coherence = calculate_metric_coherence(rhythmic_strata_home, bar_tempo_home, rhythmic_strata_home, bar_tempo_home, standard_barlow)
    cross_coherence = calculate_metric_coherence(rhythmic_strata_away, bar_tempo_away, rhythmic_strata_home, bar_tempo_home, standard_barlow)
    return cross_coherence / auto_coherence


# ------------------------------------------------- Other ---------------------------------------------------

# from Terhardt. Chosen for ease of inverse calculation
def freq_to_bark(f):
    return 13.3 * math.atan(0.75*f/1000.0)


# the inverse formula
def bark_to_freq(b):
    return math.tan(b/13.3)*1000.0/0.75
