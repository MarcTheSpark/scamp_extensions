var pythonPort = thisProcess.argv[0].asInteger;
Server.default.waitForBoot({
    var sendAddress = NetAddr.new(NetAddr.localAddr.hostname, pythonPort);
    sendAddress.sendMsg("/supercollider/port", NetAddr.langPort);
    ScampUtils.startSynthCompileListener("/compile/synth_def", sendAddress);
    ScampUtils.startRecordingListener;
    ScampUtils.startQuitListener;
})
