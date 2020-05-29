"""
Subpackage containing rhythm-related extensions. These include abstractions for representing metric structures and a
more flexible implementation of Clarence Barlow's concept of indispensability.
"""

from .indispensability import indispensability_array_from_strata, indispensability_array_from_expression, \
    barlow_style_indispensability_array
from .metric_structure import MetricStructure, MeterArithmeticGroup
