"""
Module containing the :class:`KeyPlane` class for treating the keys of the computer as a discrete, 2-dimensional
input plane.
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

import scamp
from inspect import signature
from functools import partial
from typing import Callable


class KeyPlane:

    """
    Abstraction used to transform keyboard input into a two-dimensional control space. Each key pressed corresponds
    to a vertical and horizontal position, which is passed to the callback function, along with (optionally)
    whether it was an up or down keystroke and what modifiers were present.

    :param callback: a function of the form "callback(coordinates, up_or_down, modifiers)". Can also have the
        signature "callback(coordinates, up_or_down)" or "callback(coordinates)", in which case it is simply not
        passed that information.
    :param normalize_coordinates: if True, the keys coordinates go from 0-1 horizontally and vertically. if False,
        they go from 0-3 (inclusive) vertically and 0-9, 10 or 11 horizontally (depending on row)
    :ivar modifiers_down: a list of modifier keys currently pressed
    """

    _key_codes_by_row_and_column = [
        [90, 88, 67, 86, 66, 78, 77, 188, 190, 191],
        [65, 83, 68, 70, 71, 72, 74, 75, 76, 186, 222],
        [81, 87, 69, 82, 84, 89, 85, 73, 79, 80, 219, 221],
        [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 189, 187]
    ]

    #: tuple of all names of modifier keys
    all_modifiers = ("ctrl", "alt", "shift", "cmd", "caps_lock", "tab",
                     "enter", "backspace", "up", "left", "down", "up")

    def __init__(self, callback: Callable, normalize_coordinates: bool = False):
        self.callback = callback
        self.normalize_coordinates = normalize_coordinates
        self.modifiers_down = []

    @property
    def callback(self) -> Callable:
        """
        Callback function as described in the constructor, which responds to keyboard presses.
        """
        return self._callback

    @callback.setter
    def callback(self, value):
        assert callable(value)
        self._num_callback_arguments = len(signature(value).parameters)
        assert self._num_callback_arguments > 0, "KeyPlane callback must take from one to three arguments."
        self._callback = value

    def start(self, suppress: bool = False, blocking: bool = False, session: bool = None) -> None:
        """
        Starts up the KeyPlane listening to keyboard input.

        :param suppress: if True, suppresses all other keyboard events so that nothing gets triggered unintentionally.
            (Make sure you have a way of stopping the script with the mouse!)
        :param blocking: if True causes this call to block (by calling :func:`wait_forever` on the underlying
            :class:`scamp.session.Session`).
        :param session: a :class:`scamp.session.Session` on which to run the keyboard listener. If None, looks to see
            if there's a session running on the current thread.
        """
        def key_handler(name, number, press_or_release):
            if name is None:
                # catches something weird that happens with shift-alt and shit-tab
                return

            if name.replace("_r", "") in KeyPlane.all_modifiers:
                modifier = name.replace("_r", "")
                if press_or_release == "press":
                    if modifier not in self.modifiers_down:
                        self.modifiers_down.append(modifier)
                else:
                    if modifier in self.modifiers_down:
                        self.modifiers_down.remove(modifier)

            for y, codes_row in enumerate(KeyPlane._key_codes_by_row_and_column):
                if number in codes_row:
                    x = codes_row.index(number)
                    if self.normalize_coordinates:
                        x /= len(codes_row) - 1
                        y /= 3
                    if self._num_callback_arguments > 2:
                        self.callback((x, y), press_or_release, self.modifiers_down)
                    elif self._num_callback_arguments > 1:
                        self.callback((x, y), press_or_release)
                    else:
                        self.callback((x, y))
                    return

        if session is None:
            if scamp.current_clock() is not None and isinstance(scamp.current_clock().master, scamp.Session):
                session = scamp.current_clock().master
            else:
                session = scamp.Session()

        session.register_keyboard_listener(
            on_press=partial(key_handler, press_or_release="press"),
            on_release=partial(key_handler, press_or_release="release"),
            suppress=suppress
        )
        if blocking:
            session.wait_forever()
