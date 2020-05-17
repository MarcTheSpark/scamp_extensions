from scamp_extensions.interaction import KeyPlane


def callback(coordinates, press_or_release, modifiers):
    if press_or_release == "press":
        print("Press at:", coordinates, "with modifiers", modifiers)
    else:
        print("Release at:", coordinates, "with modifiers", modifiers)


KeyPlane(callback, normalize_coordinates=True).start(blocking=True, suppress=True)
