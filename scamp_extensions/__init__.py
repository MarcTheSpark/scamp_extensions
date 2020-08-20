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

"""
Package intended to provide extra, non-core functionality to the SCAMP (Suite for Computer-Assisted Music in Python)
framework for music composition. This package is the place for models of music-theoretical concepts (e.g. scales,
pitch-class sets), conveniences for interacting with various types of input and output, and in general anything that
builds upon SCAMP but is outside of the scope of the main framework.

The package is split into several subpackages according to the nature of the content: The pitch subpackage contains
tools for manipulating pitches, such as scales and intervals; the rhythm subpackage contains tools for creating and
interacting with rhythms and meters; the interaction subpackage contains utilities for human interface devices and
other live interactions; the supercollider subpackage contains utilities for embedding supercollider code within
SCAMP scripts; and the composers subpackage contains composer-specific tools and theoretical devices.
"""