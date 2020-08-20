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

import itertools
from collections.abc import Sequence
from itertools import chain, count
from copy import deepcopy
import operator
import functools


def rotate(l, n):
    return l[n:] + l[:n]


def decompose_to_twos_and_threes(n):
    """
    Split an integer into a list of 2's and possible one 3 that add up to it

    :param n: the int
    :return: a list of 2's and possible one three
    """
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


def depth(seq):
    """
    Find the maximum depth of any element in a nested sequence. Slightly adapted from pillmuncher's answer here:
    https://stackoverflow.com/questions/6039103/counting-depth-or-the-deepest-level-a-nested-list-goes-to

    :param seq: a nested Sequence (list, tuple, etc)
    :return: int representing maximum depth
    """
    if not isinstance(seq, Sequence):
        return 0
    seq = iter(seq)
    try:
        for level in count():
            seq = chain([next(seq)], seq)
            seq = chain.from_iterable(s for s in seq if isinstance(s, Sequence))
    except StopIteration:
        return level


def normalize_depth(l, in_place=True):
    """
    Modifies a list, wrapping parts of it in new lists, so that every element is at uniform depth.

    :param l: a list
    :param in_place: if False, the original list remains unchanged
    :return: a modified version of that list with each element at uniform depth
    """
    if not in_place:
        l = deepcopy(l)

    max_depth = max(depth(element) for element in l)
    for i in range(len(l)):
        while depth(l[i]) < max_depth:
            l[i] = [l[i]]
    for element in l:
        if isinstance(element, list):
            normalize_depth(element)
    return l


class MeterArithmeticGroup:

    def __init__(self, elements, operation):
        assert operation in ("+", "*") or operation is None and len(elements) == 1 and isinstance(elements[0], int)
        self.elements = elements
        self.operation = operation

    @classmethod
    def parse(cls, input_string):
        input_string = input_string.replace(" ", "")
        if any(c in input_string for c in ("(", ")", "*", "+")):
            paren_level = 0
            chunks = []
            current_chunk = ""
            for char in input_string:
                if paren_level == 0 and char in ("+", "*"):
                    if len(current_chunk) > 0:
                        chunks.append(current_chunk)
                    current_chunk = ""
                    chunks.append(char)
                    continue
                if char == "(":
                    paren_level += 1
                    continue
                elif char == ")":
                    paren_level -= 1
                    if paren_level == 0:
                        chunks.append(current_chunk)
                        current_chunk = ""
                    continue
                current_chunk += char
            if len(current_chunk) > 0:
                chunks.append(current_chunk)

            merged_multiplies = []
            i = 0
            while i < len(chunks):
                if i + 1 < len(chunks) and chunks[i + 1] == "*":
                    multiplied_elements = chunks[i:i + 3:2]
                    i += 3
                    while i < len(chunks) and chunks[i] == "*":
                        multiplied_elements.append(chunks[i])
                        i += 2
                    merged_multiplies.append(
                        MeterArithmeticGroup([MeterArithmeticGroup.parse(x) for x in multiplied_elements], "*"))
                else:
                    merged_multiplies.append(chunks[i])
                    i += 1

            return MeterArithmeticGroup(
                [x if isinstance(x, MeterArithmeticGroup)
                 else MeterArithmeticGroup.parse(x) for x in merged_multiplies if x != "+"], "+"
            )
        else:
            return MeterArithmeticGroup([int(input_string)], None)

    def to_metric_layer(self):
        if self.operation is None:
            return MetricLayer(self.elements[0])
        elif self.operation == "+":
            return MetricLayer([x.to_metric_layer() for x in self.elements])
        else:
            return functools.reduce(operator.mul, (x.to_metric_layer() for x in self.elements))

    def __repr__(self):
        return "ArithmeticGroup({}, {})".format(self.elements, self.operation)


def break_at_operators_and_parens(s):
    s = s.replace(" ", "")
    paren_level = 0
    chunks = []
    current_chunk = ""
    for char in s:
        if paren_level == 0 and char in ("+", "*"):
            if len(current_chunk) > 0:
                chunks.append(current_chunk)
            current_chunk = ""
            chunks.append(char)
            continue
        if char == "(":
            paren_level += 1
            continue
        elif char == ")":
            paren_level -= 1
            if paren_level == 0:
                chunks.append(current_chunk)
                current_chunk = ""
            continue
        current_chunk += char
    if len(current_chunk) > 0:
        chunks.append(current_chunk)

    merged_multiplies = []
    i = 0
    while i < len(chunks):
        if i + 1 < len(chunks) and chunks[i+1] == "*":
            block = chunks[i:i+3]
            i += 3
            while i < len(chunks) and chunks[i] == "*":
                block.extend(chunks[i:i+2])
                i += 2
            merged_multiplies.append(block)
        else:
            merged_multiplies.append(chunks[i])
            i += 1

    return merged_multiplies




def get_eval_string(s):
    components = break_at_operators_and_parens(s)
    print(components)
    if len(components) == 1:
        return "MetricLayer({})".format(components[0])
    else:
        for i in range(len(components)):
            if isinstance(components[i], list):
                components[i] = "".join(x if x == "*" else get_eval_string(x) for x in components[i])
        return " | ".join(components)

print(MeterArithmeticGroup.parse("(13 + 4) + 4*5 + 6+ 2*(2 + 5 + 7 + 9)"))

def flatten_beat_groups(beat_groups, upbeats_before_group_length=True):
    """
    Returns a flattened version of beat groups, unraveling the outer layer according to rules of indispensability
    repeated application of this function to nested beat groups leads to a 1-d ordered list of beat priorities

    :param beat_groups: list of nested beat group
    :param upbeats_before_group_length: This is best explained with an example. Consider a 5 = 2 + 3 beat pattern.
        The Barlow approach to indispensability would give indispensabilities [4, 0, 3, 1, 2]. The idea would be
        downbeat first, then start of the group of 3, then upbeat to downbeat, and then the fourth eighth note because
        it's the upbeat to that upbeat, and because he would say the eighth note right after the downbeat should be the
        most dispensable. However, another way of looking at it would be to say that once we get to [4, _, 3, _, 2],
        the next most indispensable beat should be the second eighth note, since it is the pickup to the second most
        indispensable beat! This would yield indispensabilities [4, 1, 3, 0, 2], which also makes sense. I've chosen
        to make this latter approach the default; I think it generally sounds more correct.
    :return: a (perhaps still nested) list of beat groups with the outer layer unraveled so that it a layer less deep
    """
    beat_groups = deepcopy(beat_groups)
    out = []
    # first big beats
    for sub_group in beat_groups:
        out.append(sub_group.pop(0))

    if upbeats_before_group_length:
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
        regex = re.compile(r'(^|[^*0-9])(\d+(?:\+\d+)+)($|[^*0-9])')
        bob = regex.sub(lambda mo: mo.group(1) + "MetricLayer(" +mo.group(2).replace("+", ",") + ")" + mo.group(3),
                        input_string)
        # processed_string = re.sub(r'(^|[^*0-9])(\d+(?:\+\d+)+)($|[^*0-9])', r'\1addGroup(\2)\3', input_string)
        # processed_string.find("addGroup")
        # print(processed_string)
        print(bob)
        exit()
        out = eval(re.sub(r'(^|[^*])(\d+)', r"\1MetricLayer(\2)", input_string))
        assert isinstance(out, MetricLayer)
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

    def get_nested_beat_groups(self):
        beat_groups = []
        beat = 0
        for group in reversed(self.groups):
            beat_group = list(range(group)) if isinstance(group, int) else group.get_nested_beat_groups()
            MetricLayer._increment_nested_list(beat_group, beat)
            beat += MetricLayer._count_nested_list(beat_group)
            beat_groups.append(beat_group)
        return beat_groups

    def get_backward_beat_priorities(self, upbeats_before_group_length=True):
        # If some branches of the beat priorities tree don't go as far as others, we should embed
        # them further so that every beat is at the same depth within the tree
        nested_beat_groups = normalize_depth(self.get_nested_beat_groups())
        while depth(nested_beat_groups) > 1:
            nested_beat_groups = flatten_beat_groups(nested_beat_groups, upbeats_before_group_length)
        return nested_beat_groups

    def get_indispensability_array(self, upbeats_before_group_length=True):
        """
        Resolve the nested structure to a single one-dimensional indispensability array.

        :param upbeats_before_group_length: see description in flatten_beat_groups above. Affects the result when there
            are groups of uneven length at some level of metric structure. To achieve the standard Barlowian result,
            set this to False. I think it works better as True, though.
        :return: an indispensability array
        """
        backward_beat_priorities = list(self.get_backward_beat_priorities(upbeats_before_group_length))
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
        return self.join(other)
        # if isinstance(other, MetricLayer) and len(other.groups) > 1:
        #     return self.join(other)
        # else:
        #     return self.append(other, in_place=False)

    def __mul__(self, other):
        assert isinstance(other, (MetricLayer, int))
        if isinstance(other, int):
            return self * MetricLayer(other)
        else:
            return MetricLayer(*(group * other for group in self.groups))

    def __rmul__(self, other):
        assert isinstance(other, int)
        if other == 1:
            return self
        return MetricLayer(*([self] * other))

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


# Maybe scroll through for a given parentheses level
print(eval(MetricLayer.from_string("(13 + 4) + 4 + 6+ (2 + 5 + 7 + 9)")))
print(MetricLayer.from_string("3+4 + (8+2)"))
print(MetricLayer.from_string("2+2"))
MetricLayer(MetricLayer(MetricLayer(2, 2), MetricLayer(2, 2), MetricLayer(2, 2)), MetricLayer(MetricLayer(2, 2), MetricLayer(2, 2), MetricLayer(2, 2), MetricLayer(2, 2)))
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



print(MetricLayer.from_string("(3 + 2 + 4) * 2 * (2 + 3) * 4").get_indispensability_array(upbeats_before_group_length=False))
print(get_indispensability_array((4, (2, 3), 2, (3, 2, 4))))
print(MetricLayer.from_string("(3 + 2) + (2 + 2 + 3) + 3").get_indispensability_array(upbeats_before_group_length=False))
exit()