"""
Subpackage containing tools for interfacing with SuperCollider. These tools are enabled by calling
:func:`~sc_playback_implementation.add_sc_extensions`, which adds several functions to SCAMP's
:class:`~scamp.instruments.Ensemble` and :class:`~scamp.session.Session` classes. NB: All of this functionality
assumes that you have SuperCollider installed in such a way that it can be run from the command line
(via the command "sclang").
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

from .sc_playback_implementation import SCPlaybackImplementation, add_sc_extensions
from .sc_lang import SCLangInstance
