"""
Module containing the :class:`KeyPlane` class for treating the keys of the computer as a discrete, 2-dimensional
input plane.
"""

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
        [122, 120, 99, 118, 98, 110, 109, 44, 46, 47],
        [97, 115, 100, 102, 103, 104, 106, 107, 108, 59, 39],
        [113, 119, 101, 114, 116, 121, 117, 105, 111, 112, 91, 93],
        [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 45, 61]
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
