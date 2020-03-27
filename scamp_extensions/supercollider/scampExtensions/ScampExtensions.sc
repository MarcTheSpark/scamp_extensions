ScampUtilsOnTheFly {
	classvar notesPlaying;
	*instrumentFromSynthDef { |synthDef|
		var synthArgs = synthDef.func.def.argNames.asArray;
		notesPlaying.isNil.if({
			notesPlaying = Dictionary();
		});
		if(synthArgs.includes(\freq).and(synthArgs.includes(\volume)).and(synthArgs.includes(\gate)), {
			// START NOTE
			OSCFunc({ arg msg, time, addr, recvPort;
				var id = msg[1], pitch = msg[2], volume = msg[3];
				notesPlaying.put(id, Synth(synthDef.name,
					[\freq, pitch.midicps, \volume, volume, \gate, 1]
				));
			}, '/'++synthDef.name++'/start_note');
			// END NOTE
			OSCFunc({ arg msg, time, addr, recvPort;
				var id = msg[1];
				notesPlaying[id].set(\gate, 0);
			}, '/'++synthDef.name++'/end_note');
			// CHANGE PITCH
			OSCFunc({ arg msg, time, addr, recvPort;
				var id = msg[1], pitch = msg[2];
				notesPlaying[id].set(\freq, pitch.midicps);
			}, '/'++synthDef.name++'/change_pitch');
			// CHANGE VOLUME
			OSCFunc({ arg msg, time, addr, recvPort;
				var id = msg[1], volume = msg[2];
				notesPlaying[id].set(\volume, volume);
			}, '/'++synthDef.name++'/change_volume');

			// CHANGE OTHER PARAMETERS
			synthDef.func.def.argNames.do({ |argName|
				if([\freq, \volume, \gate].includes(argName).not, {
					OSCFunc({ arg msg, time, addr, recvPort;
						var id = msg[1], value = msg[2];
						notesPlaying[id].set(argName, value);
					}, '/'++synthDef.name++'/change_parameter/'++argName);
				});
			});

		}, {
			Error("SCAMP SynthDef must contain at least \freq, \volume, and \gate arguments").throw;
		});

		synthDef.add;
	}

	*startSynthCompileListener { |path, responseAddress|
	    OSCFunc({ arg msg, time, addr, recvPort;
            var synthDef = msg[1].asString.interpret;
            ScampUtilsOnTheFly.instrumentFromSynthDef(synthDef);
            {
                Server.default.sync;
                responseAddress.sendMsg("/done_compiling", 1);
            }.fork;
        }, path);
	}

	*startRecordingListener {
	    OSCFunc({ arg msg, time, addr, recvPort;
            var path = msg[1], channels = msg[2];
            Server.default.prepareForRecord(path.asString, channels);
            {
                Server.default.sync;
                Server.default.record;
            }.fork;
        }, "/recording/start");
        OSCFunc({ arg msg, time, addr, recvPort;
            Server.default.stopRecording;
        }, "/recording/stop");
	}

	*startQuitListener { |path, responseAddress|
	    OSCFunc({ arg msg, time, addr, recvPort;
            0.exit;
        }, "/quit");
	}
}
