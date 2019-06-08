from scamp.playback_implementations import OSCPlaybackImplementation
from subprocess import Popen
import socket
from threading import Event
from pythonosc import dispatcher, osc_server, udp_client
import threading


def _pick_unused_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


# def _start_supercollider():
#     """
#     Starts sclang as a daemon subprocess, incorporating the supercollider scamp utilities, and setting up a listener
#     to compile new SynthDefs and link up all the necessary OSC message handlers.
#
#     :return: the port SuperCollider is running on
#     """
#     listening_port = _pick_unused_port()
#     command = ["sclang", "-l", "./scamp_sc_config.yaml", "scInit.scd", str(listening_port), "&"]
#     Popen(command)
#
#     osc_dispatcher = dispatcher.Dispatcher()
#     sc_port = None
#     port_received = Event()
#
#     def sc_port_handler(_, port):
#         nonlocal sc_port
#         sc_port = port
#         port_received.set()
#
#     osc_dispatcher.map("/supercollider/port", sc_port_handler)
#     server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', listening_port), osc_dispatcher)
#     threading.Thread(target=server.serve_forever, daemon=True).start()
#
#     port_received.wait()
#     server.shutdown()
#     return sc_port


class SCLangInstance:

    def __init__(self):
        self._listening_port = _pick_unused_port()
        command = ["sclang", "-l", "./scamp_sc_config.yaml", "scInit.scd", str(self._listening_port), "&"]
        Popen(command)
        self.port = self.wait_for_response("/supercollider/port")

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


# _start_supercollider()
#
# print("SuperCollider ready and waiting on port", sc_port)
# exit()
#
# client = udp_client.SimpleUDPClient("127.0.0.1", sc_port)
#
# client.send_message("/compile/synth_def", [
#     r"""
#     SynthDef(\vibrato, { |out=0, freq=440, volume=0.1, gate=1, vibFreq=20, vibWidth=0.5|
#         var gain = (-40 * (1-volume)).dbamp;
#         var envelope = EnvGen.ar(Env.asr(releaseTime:0.5), gate, doneAction: 2);
#         var vibHalfSteps = SinOsc.ar(vibFreq) * vibWidth;
#         var vibFreqMul = 2.pow(vibHalfSteps / 12);
#         var vibSine =  SinOsc.ar(freq * vibFreqMul) * gain / 4;
#         Out.ar(out, (envelope * vibSine) ! 2);
#     }, [\ir, 0.1, 0.1, 0.1, 0.1, \kr])
#     """
# ])
#
# from scamp import *
#
# s = Session()
#
# vib = s.new_osc_part("vibrato", sc_port)
#
# vib.play_note(70, 1.0, 3, {"param_vibWidth": [0, 5]})


class SCPlaybackImplementation(OSCPlaybackImplementation):

    def __init__(self, host_instrument, synth_def: str):
        self.host_instrument = host_instrument
        self._resources = None
        if not self.has_shared_resource("sclang_instance"):
            self.set_shared_resource("sclang_instance", SCLangInstance())
        sclang = self.get_shared_resource("sclang_instance")

        if synth_def.isalpha() or synth_def[0] == "\\" and synth_def[1:].isalpha():
            # just the name of the synth_def
            def_name = synth_def.replace("\\", "")
            compile_synth_def = False
        else:
            def_name = synth_def.split("\\")[1].split(",")[0].strip()
            compile_synth_def = True

        super().__init__(host_instrument, sclang.port, ip_address="127.0.0.1", message_prefix=def_name)

        if compile_synth_def:
            self.client.send_message("/compile/synth_def", [synth_def])
            sclang.wait_for_response("/done_compiling")


from scamp import *

s = Session()

vib = s.new_silent_part("vibrato")
SCPlaybackImplementation(vib, r"""
    SynthDef(\vibrato, { |out=0, freq=440, volume=0.1, gate=1, vibFreq=20, vibWidth=0.5|
        var gain = (-40 * (1-volume)).dbamp;
        var envelope = EnvGen.ar(Env.asr(releaseTime:0.5), gate, doneAction: 2);
        var vibHalfSteps = SinOsc.ar(vibFreq) * vibWidth;
        var vibFreqMul = 2.pow(vibHalfSteps / 12);
        var vibSine =  SinOsc.ar(freq * vibFreqMul) * gain / 4;
        Out.ar(out, (envelope * vibSine) ! 2);
    }, [\ir, 0.1, 0.1, 0.1, 0.1, \kr])
""")

print(vib.playback_implementations)

vib.play_note(70, 1, 3, {"param_vibWidth": [0, 5]})
