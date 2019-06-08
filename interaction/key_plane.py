from pynput.keyboard import Listener
from inspect import signature
from functools import partial


class KeyPlane:

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

    def __init__(self, callback, normalize_coordinates=False):
        """
        :param callback: a function of the form "callback(coordinates, up_or_down, modifiers)". Can also have the
        signature "callback(coordinates, up_or_down)" or "callback(coordinates)", in which case it is simply not
        passed that information.
        :param normalize_coordinates: if True, the keys coordinates go from 0-1 horizontally and vertically. if False,
        they go from 0-3 (inclusive) vertically and 0-9, 10 or 11 horizontally (depending on row)
        """
        self.callback = callback
        self.normalize_coordinates = normalize_coordinates

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        assert callable(value)
        self._num_callback_arguments = len(signature(value).parameters)
        assert self._num_callback_arguments > 0, "KeyPlane callback must take from one to three arguments."
        self._callback = value

    def start(self, blocking=False):
        def handle_key(key, press_or_release):
            try:
                key_code = ord(key.char)
                for modifiers, key_codes_by_row_and_column in KeyPlane.key_codes_by_modifier_row_and_column:
                    for y, codes_row in enumerate(key_codes_by_row_and_column):
                        if key_code in codes_row:
                            x = codes_row.index(key_code)
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

        if blocking:
            # Collect events until released
            with Listener(
                    on_press=partial(handle_key, press_or_release="press"),
                    on_release=partial(handle_key, press_or_release="release")) as listener:
                listener.join()
        else:
            Listener(on_press=partial(handle_key, press_or_release="press"),
                     on_release=partial(handle_key, press_or_release="release")).start()
