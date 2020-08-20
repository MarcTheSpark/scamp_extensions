"""
Contains the :class:`MetricStructure` class, which provides a highly flexible representation of metric hierarchy.
The easiest and most flexible way of creating MetricStructures is through the :func:`~MetricStructure.from_string`
method, which makes use of the :class:`MeterArithmeticGroup` class to parse expressions like "(2 + 3 + 2) * 3"
(which would representing a 6/8 + 9/8 + 6/8 additive compound meter).
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

# The metric structure module is used within the main SCAMP library behind the scenes, but doesn't really make sense
# as part of the public interface. It really feels more like an extension, which is why it is included here.
from scamp._metric_structure import *
