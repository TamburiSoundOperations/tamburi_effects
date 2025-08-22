// --- Boot del server e setup ---
s.waitForBoot({
    // Carica i buffer (modifica i path se necessario)
    ~bufs = IdentityDictionary[
        17 -> Buffer.read(s, "sounds/Jah Shaka - Jah Shaka answers - 01 1.wav"),
        27 -> Buffer.read(s, "sounds/Jah Shaka - Jah Shaka answers - 02 2.wav"),
        22 -> Buffer.read(s, "sounds/Jah Shaka - Jah Shaka answers - 03 3.wav")
    ];

    SynthDef(\playBuf, { |buf, amp = 1|
        var sig = PlayBuf.ar( // mono -> stereo
            numChannels: 1,
            bufnum: buf,
            rate: BufRateScale.kr(buf),
            doneAction: 2
        );
        Out.ar(0, (sig ! 2) * amp);
    }).add;

    ~players = Group.new;   // tutti i player qui dentro
    s.sync;

    // --- Handlers OSC ---
    // /play, pin:int [, amp:float]
    OSCdef(\play, { |msg|
        var pin = msg[1].asInteger;
        var amp = if(msg.size > 2, { msg[2].asFloat.clip(0, 1) }, { 1.0 });
        var buf = ~bufs[pin];
        if(buf.notNil, {
            Synth.tail(~players, \playBuf, [\buf, buf.bufnum, \amp, amp]);
            ("PLAY from pin %" ).format(pin).postln;
        }, {
            ("No buffer for pin %").format(pin).warn;
        });
    }, '/play');

    // /pause  e  /resume  via mute/unmute del server (comodo come “pausa globale”)
    OSCdef(\pause,  { s.mute;   "PAUSE".postln;  }, '/pause');
    OSCdef(\resume, { s.unmute; "RESUME".postln; }, '/resume');

    // /stop -> ferma tutti i player attivi
    OSCdef(\stop, { ~players.freeAll; "STOP".postln; }, '/stop');

    "Ready: OSC on 57120 (/play, /pause, /resume, /stop)".postln;
});

// Pulizia quando fermi (Cmd+.)
CmdPeriod.doOnce({
    if(~players.notNil) { ~players.freeAll };
    if(~bufs.notNil) { ~bufs.values.do(_.free) };
});
