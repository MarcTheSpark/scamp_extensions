"""
Subpackage containing rhythm-related extensions. These include abstractions for representing metric structures, a
more flexible implementation of Clarence Barlow's concept of indispensability, and a boolean streamer module that
implements, among other things, a Xenakian sieve rhythms.
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

from .indispensability import indispensability_array_from_strata, indispensability_array_from_expression, \
    barlow_style_indispensability_array
from .metric_structure import MetricStructure, MeterArithmeticGroup
from .boolean_streamer import boolean_streamer, BooleanStreamer, SieveStreamer, RandStreamer, FreqStreamer
