from scamp_extensions.key_plane import KeyPlane


def callback(coordinates, press_or_release, modifiers):
    if press_or_release == "press":
        print(modifiers.upper(), "Press at:", coordinates)
    else:
        print(modifiers.upper(), "Release at:", coordinates)


bob = KeyPlane(callback, normalize_coordinates=True)
bob.start(True)
