"""
Module containing functionality for starting up and communicating with an instance of sclang. (Note that this assumes
that SuperCollider is installed and can be run from the command line.)
"""

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
    """
    Object that starts up an instance of sclang as a subprocess, and facilitates communication with that subprocess
    via OSC. The SCAMP supercollider extensions will be loaded into the sclang library path.
    """

    def __init__(self):
        self._listening_port = _pick_unused_port()
        command = ["sclang", "-l", os.path.join(module_dir, "./scamp_sc_config.yaml"),
                   os.path.join(module_dir, "scInit.scd"), str(self._listening_port)]
        Popen(command, cwd=module_dir)
        self.port = self.wait_for_response("/supercollider/port")
        self._client = udp_client.SimpleUDPClient("127.0.0.1", self.port)
        atexit.register(lambda: self.send_message("/quit", 0))

    def send_message(self, address, value) -> None:
        """
        Sends an OSC message to the running instance of sclang.

        :param address: the osc address string
        :param value: the message value
        """
        self._client.send_message(address, value)

    def wait_for_response(self, address) -> str:
        """
        Waits for a response from sclang to be sent to the given address, confirming that we are on the same page and
        telling us what address to send messages to.

        :param address: the OSC message address at which to expect the response.
        """
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

    def new_synth_def(self, synth_def_code: str) -> None:
        r"""
        Sends the given SynthDef to SuperCollider to compile and add to the server.

        :param synth_def_code: the sclang code for the SynthDef (i.e. "SynthDef(\nameOFSynth, {[ugen graph function]}").
        """
        self.send_message("/compile/synth_def", [synth_def_code])
        self.wait_for_response("/done_compiling")

