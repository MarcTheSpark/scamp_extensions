"""
Re-implementation and extension of Clarence Barlow's concept of rhythmic indispensability such that it works for
additive meters (even nested additive meters).
"""

from .metric_structure import MeterArithmeticGroup


def indispensability_array_from_expression(meter_arithmetic_expression: str, normalize=False,
                                           split_large_numbers=False, upbeats_before_group_length=True):
    return MeterArithmeticGroup.parse(meter_arithmetic_expression) \
        .to_metric_structure(split_large_numbers) \
        .get_indispensability_array(normalize=normalize, upbeats_before_group_length=upbeats_before_group_length)


def indispensability_array_from_strata(*rhythmic_strata, normalize=False,
                                       split_large_numbers=False, upbeats_before_group_length=True):
    expression = "*".join(
        ("("+"+".join(str(y) for y in x)+")" if hasattr(x, "__len__") else str(x)) for x in rhythmic_strata
    )
    return indispensability_array_from_expression(
        expression, normalize=normalize, split_large_numbers=split_large_numbers,
        upbeats_before_group_length=upbeats_before_group_length
    )


def barlow_style_indispensability_array(*rhythmic_strata, normalize=False):
    if not all(isinstance(x, int) for x in rhythmic_strata):
        raise ValueError("Standard Barlow indispensability arrays must be based on from integer strata.")
    return indispensability_array_from_expression("*".join(str(x) for x in rhythmic_strata), normalize=normalize,
                                                  split_large_numbers=True, upbeats_before_group_length=False)
