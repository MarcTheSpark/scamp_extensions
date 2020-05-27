"""
Contains the :class:`MetricStructure` class, which provides a highly flexible representation of metric hierarchy.
The easiest and most flexible way of creating MetricStructures is through the :func:`~MetricStructure.from_string`
method, which makes use of the :class:`MeterArithmeticGroup` class to parse expressions like "(2 + 3 + 2) * 3"
(which would representing a 6/8 + 9/8 + 6/8 additive compound meter).
"""

# The metric structure module is used within the main SCAMP library behind the scenes, but doesn't really make sense
# as part of the public interface. It really feels more like an extension, which is why it is included here.
from scamp._metric_structure import *
