"""
Module containing the :class:`SCPlaybackImplementation` class (an extension of
:class:`~scamp.playback_implementations.OSCPlaybackImplementation`), which can be added to an instance of
:class:`~scamp.instruments.ScampInstrument`.
"""

from scamp.playback_implementations import OSCPlaybackImplementation
from .sc_lang import SCLangInstance
from scamp.instruments import ScampInstrument, Ensemble


class SCPlaybackImplementation(OSCPlaybackImplementation):

    """
    A subclass of :class:`~scamp.playback_implementations.OSCPlaybackImplementation` designed to communicate with
    a running copy of SCLang (via an :class:`~scamp_extensions.supercollider.sc_lang.SCLangInstance`).

    :param host_instrument: the host instrument for this playback implementation
    :param synth_def: a string of SCLang code representing the SynthDef to run. This should take at least the
        the arguments "freq" (to which the pitch is sent), "volume" (to which the not volume is sent), and "gate"
        (which is used to start and stop the note).
    """

    def __init__(self, host_instrument, synth_def: str):
        self._host_instrument = host_instrument
        if not self.has_shared_resource("sclang_instance"):
            self.set_shared_resource("sclang_instance", SCLangInstance())
        sclang = self.get_shared_resource("sclang_instance")

        if synth_def.isalnum() or synth_def[0] == "\\" and synth_def[1:].isalnum():
            # just the name of the synth_def
            def_name = synth_def.replace("\\", "")
            compile_synth_def = False
        else:
            def_name = synth_def.split("\\")[1].split(",")[0].strip()
            compile_synth_def = True

        super().__init__(host_instrument, sclang.port, ip_address="127.0.0.1", message_prefix=def_name)

        if compile_synth_def:
            sclang.new_synth_def(synth_def)


def add_sc_extensions():
    """
    Adds several new functions to the :class:`~scamp.instruments.ScampInstrument` class, as well as to the
    :class:`~scamp.instruments.Ensemble` (and therefore :class:`~scamp.session.Session`).

    New instance methods of `ScampInstrument`:

    ``add_supercollider_playback(self, synth_def: str)``: takes a string containing a SuperCollider SynthDef, and adds a
    :class:`SCPlaybackImplementation` to this instrument that uses that SynthDef to synthesize sound. (This starts
    up instances of sclang and scsynth in the background.)

    ``remove_supercollider_playback(self)``: removes the (most recently added) :class:`SCPlaybackImplementation` from
    this instrument's playback_implementations.

    New instance methods of `Ensemble` / `Session`:

    ``new_supercollider_part(self, name: str, synth_def: str)``: Similarly to any of the other "new_part" methods, this
    adds and returns a newly created ScampInstrument that uses an :class:`SCPlaybackImplementation` based on the
    given synth def string.

    ``get_sclang_instance(self)``: Returns the instance of :class:`SCLangInstance` that this ensemble is using for
    supercollider playback (or creates one if none is running).

    ``start_recording_sc_output(self, path, num_channels=2)``: Tells SuperCollider to start recording the playback to
    and audio file at the given path, using the specified number of channels.

    ``stop_recording_sc_output(self)``: Stops recording SuperCollider playback to an audio file.

    """
    def _add_supercollider_playback(self, synth_def):
        SCPlaybackImplementation(self, synth_def)
        return self

    def _remove_supercollider_playback(self):
        for index in reversed(range(len(self.playback_implementations))):
            if isinstance(self.playback_implementations[index], SCPlaybackImplementation):
                self.playback_implementations.pop(index)
                break
        return self

    ScampInstrument.add_supercollider_playback = _add_supercollider_playback
    ScampInstrument.remove_supercollider_playback = _remove_supercollider_playback

    def _new_supercollider_part(self, name=None, synth_def=None):
        assert synth_def is not None
        name = "Track " + str(len(self.instruments) + 1) if name is None else name

        instrument = self.new_silent_part(name)
        instrument.add_supercollider_playback(synth_def)

        return instrument

    Ensemble.new_supercollider_part = _new_supercollider_part

    def _get_sc_instance(self):
        if SCPlaybackImplementation in self.shared_resources:
            if "sclang_instance" in self.shared_resources[SCPlaybackImplementation]:
                return self.shared_resources[SCPlaybackImplementation]["sclang_instance"]
            else:
                new_sc_instance = SCLangInstance()
                self.shared_resources[SCPlaybackImplementation]["sclang_instance"] = SCLangInstance()
        else:
            new_sc_instance = SCLangInstance()
            self.shared_resources[SCPlaybackImplementation] = {"sclang_instance": new_sc_instance}
        return new_sc_instance

    Ensemble.get_sclang_instance = _get_sc_instance

    def _start_recording_sc_output(self, path, num_channels=2):
        self.get_sclang_instance().send_message("/recording/start", [path, num_channels])

    def _stop_recording_sc_output(self):
        self.get_sclang_instance().send_message("/recording/stop", 0)

    Ensemble.start_recording_sc_output = _start_recording_sc_output
    Ensemble.stop_recording_sc_output = _stop_recording_sc_output
