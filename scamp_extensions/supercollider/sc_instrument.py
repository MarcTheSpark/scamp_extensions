from scamp.playback_implementations import OSCPlaybackImplementation
from scamp.instruments import ScampInstrument, Ensemble
from subprocess import Popen
import socket
from threading import Event
from pythonosc import dispatcher, osc_server, udp_client
import threading
import inspect
import os
import atexit


module_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def _pick_unused_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


class SCLangInstance:

    def __init__(self):
        self._listening_port = _pick_unused_port()
        command = ["sclang", "-l", os.path.join(module_dir, "./scamp_sc_config.yaml"),
                   os.path.join(module_dir, "scInit.scd"), str(self._listening_port)]
        Popen(command, cwd=module_dir)
        self.port = self.wait_for_response("/supercollider/port")
        self._client = udp_client.SimpleUDPClient("127.0.0.1", self.port)
        atexit.register(lambda: self.send_message("/quit", 0))

    def send_message(self, address, value):
        self._client.send_message(address, value)

    def wait_for_response(self, address):
        osc_dispatcher = dispatcher.Dispatcher()
        response = None
        response_received = Event()

        def response_handler(_, message):
            nonlocal response
            response = message
            response_received.set()

        osc_dispatcher.map(address, response_handler)
        server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', self._listening_port), osc_dispatcher)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        response_received.wait()
        server.shutdown()
        return response

    def new_synth_def(self, synth_def_code: str):
        self.send_message("/compile/synth_def", [synth_def_code])
        self.wait_for_response("/done_compiling")


class SCPlaybackImplementation(OSCPlaybackImplementation):

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
