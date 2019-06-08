"""
Re-implementation and extension of Clarence Barlow's concept of rhythmic indispensibility such that it works for
additive meters (even nested additive meters).
"""

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


def normalize_depth(input_list, in_place=True):
    """
    Modifies a list, wrapping parts of it in new lists, so that every element is at uniform depth.

    :param input_list: a list
    :param in_place: if False, the original list remains unchanged
    :return: a modified version of that list with each element at uniform depth
    """
    if not in_place:
        input_list = deepcopy(input_list)

    max_depth = max(depth(element) for element in input_list)
    for i in range(len(input_list)):
        while depth(input_list[i]) < max_depth:
            input_list[i] = [input_list[i]]
    for element in input_list:
        if isinstance(element, list):
            normalize_depth(element)
    return input_list


class MeterArithmeticGroup:

    def __init__(self, elements, operation):
        """
        This class exists as an aid to parsing arithmetic expressions into MetricLayers.
        The basic issue was that I didn't want addition to be associative; there needed to be a difference between
        (4 + 2) + 3, 4 + (2 + 3), and 4 + 2 + 3. The first two establish a hierarchy, while the latter places each
        group on an even footing.

        :param elements: a list of MeterArithmeticGroups
        :param operation: either "+", "*", or None, in the case of just a number
        """
        assert operation in ("+", "*") or operation is None and len(elements) == 1 and isinstance(elements[0], int)
        self.elements = elements
        self.operation = operation

    @classmethod
    def parse(cls, input_string):
        """
        Parses an input string containing an arithmetic expression into a (probably nested) MeterArithmeticGroup

        :param input_string: input string consisting of integers, plus signs, multiplication signs, and parentheses
        :return: a MeterArithmeticGroup
        """
        input_string = input_string.replace(" ", "")
        assert len(input_string) > 0, "Cannot parse empty input string."
        assert all(x in "0123456789+*()" for x in input_string), \
            "Meter arithmetic expression can only contain integers, plus signs, multiplication signs, and parentheses"
        assert input_string[0] in "(0123456789" and input_string[-1] in ")0123456789", \
            "Bad input string: leading or trailing operator."
        assert not any(x in input_string for x in ("++", "+*", "*+", "**")), \
            "Cannot parse input string: multiple adjacent operators found."
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
                    if paren_level == 1:
                        # don't include the outer level of parentheses
                        continue
                elif char == ")":
                    paren_level -= 1
                    assert paren_level >= 0, "Nonsensical parentheses detected."
                    if paren_level == 0:
                        chunks.append(current_chunk)
                        current_chunk = ""
                    if paren_level == 0:
                        # don't include the outer level of parentheses
                        continue
                current_chunk += char
            if len(current_chunk) > 0:
                chunks.append(current_chunk)

            assert paren_level == 0, "Nonsensical parentheses detected. Probably missing a close-paren."

            merged_multiplies = []
            i = 0
            while i < len(chunks):
                if i + 1 < len(chunks) and chunks[i + 1] == "*":
                    multiplied_elements = chunks[i:i + 3:2]
                    i += 3
                    while i < len(chunks) and chunks[i] == "*":
                        multiplied_elements.append(chunks[i + 1])
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

    def to_metric_layer(self, break_up_large_numbers=False):
        if self.operation is None:
            return MetricLayer(self.elements[0], break_up_large_numbers=break_up_large_numbers)
        elif self.operation == "+":
            return MetricLayer(*[x.to_metric_layer(break_up_large_numbers) for x in self.elements],
                               break_up_large_numbers=break_up_large_numbers)
        else:
            return functools.reduce(operator.mul, (x.to_metric_layer(break_up_large_numbers) for x in self.elements))

    def __repr__(self):
        return "ArithmeticGroup({}, \"{}\")".format(self.elements, self.operation)


def flatten_beat_groups(beat_groups, upbeats_before_group_length=True):
    """
    Returns a flattened version of beat groups, unraveling the outer layer according to rules of indispensibility
    repeated application of this function to nested beat groups leads to a 1-d ordered list of beat priorities

    :param beat_groups: list of nested beat group
    :param upbeats_before_group_length: This is best explained with an example. Consider a 5 = 2 + 3 beat pattern.
        The Barlow approach to indispensibility would give indispensabilities [4, 0, 3, 1, 2]. The idea would be
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

    # then by the longest chain, and secondarily by order (big beat indispensibility)
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

    def __init__(self, *groups, break_up_large_numbers=False):
        """
        A single metric layer formed by the additive concatenation of the given groups. These groups can themselves
        be metric layers, which allows for nested additive structures.

        :param groups: list of additively combined groups. If all integers, then this is like a simple additive meter
            without considering subdivisions. For instance, (2, 4, 3) is like the time signature (2+4+3)/8. However,
            any component of this layer can instead be itself a MetricLayer, allowing for nesting.
        :param break_up_large_numbers: if True, groups with number greater than 3 are broken up into a sum of 2's
            followed by one 3 if odd. This is the Barlow approach.
        Each one can either be a number or a Metric layer
        """
        assert all(isinstance(x, (int, MetricLayer))for x in groups), \
            "Metric layer groups must either be integers or metric groups themselves"

        self.groups = list(groups)

        if break_up_large_numbers:
            self.break_up_large_numbers()

        self._remove_redundant_nesting()

    @classmethod
    def from_string(cls, input_string: str, break_up_large_numbers=False):
        return MeterArithmeticGroup.parse(input_string).to_metric_layer(break_up_large_numbers)

    def break_up_large_numbers(self):
        for i, group in enumerate(self.groups):
            if isinstance(group, int):
                if group > 3:
                    self.groups[i] = MetricLayer(*decompose_to_twos_and_threes(group))
            else:
                self.groups[i].break_up_large_numbers()
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

    def get_indispensibility_array(self, upbeats_before_group_length=True, normalize=False):
        """
        Resolve the nested structure to a single one-dimensional indispensibility array.

        :param upbeats_before_group_length: see description in flatten_beat_groups above. Affects the result when there
            are groups of uneven length at some level of metric structure. To achieve the standard Barlowian result,
            set this to False. I think it works better as True, though.
        :param normalize: if True, indispensabilities range from 0 to 1. If false, they count up from 0.
        :return: an indispensibility array
        """
        backward_beat_priorities = list(self.get_backward_beat_priorities(upbeats_before_group_length))
        length = len(backward_beat_priorities)
        backward_indispensibility_array = [length - 1 - backward_beat_priorities.index(i) for i in range(length)]
        indispensibility_array = rotate(backward_indispensibility_array, 1)
        indispensibility_array.reverse()
        if normalize:
            max_val = max(indispensibility_array)
            return [float(x) / max_val for x in indispensibility_array]
        else:
            return indispensibility_array

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


def indispensibility_array_from_expression(meter_arithmetic_expression: str, normalize=False,
                                           split_large_numbers=False, upbeats_before_group_length=True):
    return MeterArithmeticGroup.parse(meter_arithmetic_expression) \
        .to_metric_layer(split_large_numbers) \
        .get_indispensibility_array(normalize=normalize, upbeats_before_group_length=upbeats_before_group_length)


def indispensibility_array_from_strata(*rhythmic_strata, normalize=False,
                                       split_large_numbers=False, upbeats_before_group_length=True):
    expression = "*".join(
        ("("+"+".join(str(y) for y in x)+")" if hasattr(x, "__len__") else str(x)) for x in rhythmic_strata
    )
    return indispensibility_array_from_expression(
        expression, normalize=normalize, split_large_numbers=split_large_numbers,
        upbeats_before_group_length=upbeats_before_group_length
    )


def barlow_style_indispensibility_array(*rhythmic_strata, normalize=False):
    assert all(isinstance(x, int) for x in rhythmic_strata), \
        "Standard Barlow indispensibility arrays must be based on from integer strata."
    return indispensibility_array_from_expression("*".join(str(x) for x in rhythmic_strata), normalize=normalize,
                                                  split_large_numbers=True, upbeats_before_group_length=False)