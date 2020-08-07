#  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  #
#  SCAMP (Suite for Computer-Assisted Music in Python)                                           #
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

from pynput.keyboard import Listener
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
    """

    key_codes_by_modifier_row_and_column = [
        ("", [
            [122, 120, 99, 118, 98, 110, 109, 44, 46, 47],
            [97, 115, 100, 102, 103, 104, 106, 107, 108, 59, 39],
            [113, 119, 101, 114, 116, 121, 117, 105, 111, 112, 91, 93],
            [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 45, 61]
        ]),
        ("shift", [
            [90, 88, 67, 86, 66, 78, 77, 60, 62, 63],
            [65, 83, 68, 70, 71, 72, 74, 75, 76, 58, 34],
            [81, 87, 69, 82, 84, 89, 85, 73, 79, 80, 123, 125],
            [33, 64, 35, 36, 37, 94, 38, 42, 40, 41, 95, 43]
        ])
    ]

    def __init__(self, callback: Callable, normalize_coordinates: bool = False):
        self.callback = callback
        self.normalize_coordinates = normalize_coordinates

    @property
    def callback(self):
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

    def start(self, blocking=False, suppress=False, bound_session=None):

        def key_name_and_number_handler(name, number, press_or_release):
            try:
                for modifiers, key_codes_by_row_and_column in KeyPlane.key_codes_by_modifier_row_and_column:
                    for y, codes_row in enumerate(key_codes_by_row_and_column):
                        if number in codes_row:
                            x = codes_row.index(number)
                            if self.normalize_coordinates:
                                x /= len(codes_row) - 1
                                y /= 3
                            if self._num_callback_arguments > 2:
                                self.callback((x, y), press_or_release, modifiers)
                            elif self._num_callback_arguments > 1:
                                self.callback((x, y), press_or_release)
                            else:
                                self.callback((x, y))
                            return
            except AttributeError:
                pass

        def key_handler(key, press_or_release):
            key_name_and_number_handler(None, ord(key.char), press_or_release)

        if bound_session is None:
            try:
                import scamp
                if scamp.current_clock() is not None and isinstance(scamp.current_clock().master, scamp.Session):
                    bound_session = scamp.current_clock().master
            except ImportError:
                bound_session = scamp = None

        if bound_session is not None:
            bound_session.register_keyboard_listener(
                on_press=partial(key_name_and_number_handler, press_or_release="press"),
                on_release=partial(key_name_and_number_handler, press_or_release="release"),
                suppress=suppress
            )
        else:
            if blocking:
                # Collect events until released
                with Listener(
                        on_press=partial(key_handler, press_or_release="press"),
                        on_release=partial(key_handler, press_or_release="release"),
                        suppress=suppress) as listener:
                    listener.join()
            else:
                Listener(on_press=partial(key_handler, press_or_release="press"),
                         on_release=partial(key_handler, press_or_release="release"),
                         suppress=suppress).start()
