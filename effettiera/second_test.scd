////////////////////////////////////////////////////////////
// GLOBAL DELAY + 3 SIRENS + MASTER VOL  (PLUGIN-FREE)
//
// Delay OSC:
//   /delay/time <sec>   (0.03..2.0)  smooth
//   /delay/fb   <0..0.92>
//   /delay/clear
//
// Master:
//   /master/vol <0..1>  FAST
//
// Siren v1 (Dub):
//   /siren/toggle
//   /siren/stop
//   /siren/freq  <500..5000>
//   /siren/rate  <0.05..5>
//   /siren/depth <0..1>
//
// Siren v2 (Air-raid Formant horn):
//   /air/toggle
//   /air/stop
//   /air/freq  <200..2000>
//   /air/rate  <0.05..1.5>
//   /air/depth <0..1>
//
// Siren v3 (BENIDUB BIP BIP):
//   /bens/toggle
//   /bens/stop
//   /bens/freq  <500..5000>   pitch
//   /bens/rate  <0.5..12>     beeps/sec
//   /bens/tone  <0..1>        sine -> buzzy
//   /bens/drive <0..1>        punch
////////////////////////////////////////////////////////////

(
~oscPort = 57120;

s.waitForBoot({

    if(thisProcess.openUDPPort(~oscPort).not) {
        ("WARNING: couldn't open UDP port " ++ ~oscPort ++ " (maybe already in use)").postln;
    } {
        ("[SC] Listening OSC on UDP port " ++ ~oscPort).postln;
    };

    s.freeAll;
    OSCdef.freeAll;

    if(~fxBus.notNil) { ~fxBus.free };
    if(~masterBus.notNil) { ~masterBus.free };

    ~fxBus = Bus.audio(s, 2);
    ~masterBus = Bus.audio(s, 2);

    // ---------------- MASTER OUT ----------------
    SynthDef(\masterOut, { |inbus=0, out=0, vol=0.25, volLag=0.002|
        var sig = In.ar(inbus, 2);
        var v = VarLag.kr(vol.clip(0.0, 1.0), volLag.clip(0.0, 0.2), warp: \lin);
        sig = sig * v;
        sig = Limiter.ar(sig, 0.98);
        Out.ar(out, sig);
    }).add;

    // ---------------- GLOBAL DUB DELAY (SMOOTH) ----------------
    SynthDef(\dubDelay, { |inbus=0, out=0,
        time=0.33, fb=0.55, mix=1.0, level=1.0,
        hp=160, lp=3800, damp=0.45,
        drive=1.6, wobble=0.002, wobRate=0.25,
        clear=0,
        timeLag=0.35, fbLag=0.20,
        dlyLag=0.04
    |
        var in, dry, loop, mod;
        var timeSm, fbSm, dlyTarget, dly;
        var clearTrig, loopGain;
        var fbSig, wet, sig;

        clearTrig = Trig1.kr(clear, 0.06);
        loopGain  = 1 - clearTrig;

        timeSm = VarLag.kr(time.clip(0.03, 2.0), timeLag.clip(0, 2), warp: \lin);
        fbSm   = VarLag.kr(fb.clip(0.0, 0.92),   fbLag.clip(0, 2),   warp: \lin);

        in  = In.ar(inbus, 2);
        dry = in;

        mod = SinOsc.kr(wobRate.clip(0.01, 10), 0, wobble.clip(0, 0.02));
        dlyTarget = (timeSm + mod).clip(0.03, 2.0);
        dly = Lag.kr(dlyTarget, dlyLag.clip(0, 0.2));

        loop  = LocalIn.ar(2);
        fbSig = in + (loop * loopGain);

        fbSig = HPF.ar(fbSig, hp.clip(20, 5000));
        fbSig = LPF.ar(fbSig, lp.clip(200, 20000));
        fbSig = LPF.ar(fbSig, (lp * (1 - (damp.clip(0,1) * 0.7))).clip(200, 20000));

        fbSig = tanh(fbSig * drive.clip(0.1, 10));

        wet = DelayC.ar(fbSig, 2.0, dly);
        LocalOut.ar(wet * fbSm * loopGain);

        sig = XFade2.ar(dry, wet, (mix.clip(0,1) * 2 - 1)) * level;
        sig = Limiter.ar(sig, 0.98);

        Out.ar(out, sig);
    }).add;

    // ---------------- SIREN 1 (DUB) ----------------
    SynthDef(\dubSiren_immediate, { |
        outDry=0, outSend=0,
        dryLevel=0.10, sendLevel=0.18,
        amp=1.0,

        freq=1000, freqLag=0.12,
        freqMin=500, freqMax=5000,

        rate=0.6, rateLag=0.15,
        rateMin=0.05, rateMax=5.0,

        depth=0.55, depthLag=0.15,

        decay=0.4,
        vibr=5.0, vibrDepth=0.006,
        dist=0.25,
        hp=120, lp=3200,
        wobble=0.12, wobbleRate=0.22,
        pan=0.0, gate=1
    |
        var env, sweep, vibrato, f;
        var freqSm, rateSm, depthSm, sweepDepth;
        var osc, driven, lpSig, hpSig, outSig;
        var ampSm, drySm, sendSm;

        env = EnvGen.ar(Env.asr(0.015, 1.0, decay), gate, doneAction:2);

        ampSm  = Lag.kr(amp, 0.02);
        drySm  = Lag.kr(dryLevel, 0.02);
        sendSm = Lag.kr(sendLevel, 0.02);

        freqSm = VarLag.kr(freq.clip(freqMin, freqMax), freqLag.clip(0.0, 2.0), warp: \exp);
        rateSm = VarLag.kr(rate.clip(rateMin, rateMax), rateLag.clip(0.0, 2.0), warp: \exp);

        depthSm = VarLag.kr(depth.clip(0.0, 1.0), depthLag.clip(0.0, 2.0), warp: \lin);
        sweepDepth = depthSm.linexp(0, 1, 0.15, 2.8);

        sweep   = LFTri.kr(rateSm).range(-1, 1);
        vibrato = SinOsc.kr(vibr) * vibrDepth;

        f = (freqSm * (1 + sweepDepth * sweep)).clip(30, 12000) * (1 + vibrato);

        osc = VarSaw.ar(f, 0, 0.5);
        driven = tanh(osc * (1 + (dist * 2)));

        lpSig = LPF.ar(driven, lp.clip(500, 12000)
            + (LFPar.kr(wobbleRate).range(0, wobble) * lp));
        hpSig = HPF.ar(lpSig, hp.max(20));

        outSig = Pan2.ar(hpSig, pan);
        outSig = LeakDC.ar(outSig);
        outSig = HPF.ar(outSig, 20);

        outSig = outSig * ampSm * env;
        outSig = Limiter.ar(outSig, 0.98);

        Out.ar(outDry,  outSig * drySm);
        Out.ar(outSend, outSig * sendSm);
    }).add;

    // ---------------- SIREN 2 (AIR RAID FORMANT) ----------------
    SynthDef(\airRaidSiren, { |
        outDry=0, outSend=0,
        dryLevel=0.07, sendLevel=0.16,
        amp=1.0,

        freq=450, freqLag=0.10,
        freqMin=200, freqMax=2000,

        rate=0.18, rateLag=0.20,
        rateMin=0.05, rateMax=1.5,

        depth=0.60, depthLag=0.20,

        riseDuty=0.78,
        depthRatio=9.0, depthRatioLag=0.20,

        tone=0.35,
        grit=0.18,
        res=0.35, resQ=0.55,
        fm=0.008, fmRate=0.22,
        hp=70, lp=3200,

        attack=0.02, release=0.7,
        pan=0.0, gate=1
    |
        var env;
        var freqSm, rateSm, depthCtlSm;
        var dutySm, resSm, resQSm, gritSm, toneSm;
        var fmSm, fmRateSm, hpSm, lpSm;
        var depthBaseSm, depthSpan;

        var ph, up, down, x, curve;
        var ratio, f, aFollow;
        var sig, extra1, outSig;
        var ampSm, drySm, sendSm;

        env = EnvGen.ar(Env.asr(attack.clip(0.002, 0.2), 1.0, release.clip(0.02, 5.0)), gate, doneAction:2);

        ampSm  = Lag.kr(amp, 0.02);
        drySm  = Lag.kr(dryLevel, 0.02);
        sendSm = Lag.kr(sendLevel, 0.02);

        freqSm  = VarLag.kr(freq.clip(freqMin, freqMax), freqLag.clip(0.0, 2.0), warp: \exp);
        rateSm  = VarLag.kr(rate.clip(rateMin, rateMax), rateLag.clip(0.0, 2.0), warp: \exp);

        depthCtlSm = VarLag.kr(depth.clip(0.0, 1.0), depthLag.clip(0.0, 2.0), warp: \lin);

        dutySm  = Lag.kr(riseDuty.clip(0.52, 0.88), 0.08);
        resSm   = Lag.kr(res.clip(0.0, 1.0), 0.10);
        resQSm  = Lag.kr(resQ.clip(0.05, 0.95), 0.10);
        gritSm  = Lag.kr(grit.clip(0.0, 1.0), 0.10);
        toneSm  = Lag.kr(tone.clip(0.0, 1.0), 0.10);

        fmSm     = Lag.kr(fm.clip(0.0, 0.05), 0.12);
        fmRateSm = VarLag.kr(fmRate.clip(0.05, 2.0), 0.25, warp: \exp);

        hpSm = VarLag.kr(hp.clip(20, 5000), 0.20, warp: \exp);
        lpSm = VarLag.kr(lp.clip(200, 16000), 0.20, warp: \exp);

        depthBaseSm = VarLag.kr(depthRatio.clip(1.0, 12.0), depthRatioLag.clip(0.0, 2.0), warp: \lin);
        depthSpan = (depthBaseSm + depthCtlSm.linlin(0, 1, 0.0, 5.0)).clip(1.0, 12.0);

        resSm  = (resSm  + depthCtlSm * 0.35).clip(0.0, 1.0);
        gritSm = (gritSm + depthCtlSm * 0.25).clip(0.0, 1.0);
        lpSm   = (lpSm + depthCtlSm.linlin(0,1, 0, 3500)).clip(300, 16000);

        ph = Phasor.kr(0, rateSm / SampleRate.ir, 0, 1, 0);

        up   = (ph / dutySm).clip(0, 1);
        down = (1 - ((ph - dutySm) / (1 - dutySm))).clip(0, 1);
        x = Select.kr(ph < dutySm, [down, up]);
        curve = x.pow(1.7);

        ratio = curve.linexp(0, 1, 1.0, depthSpan);
        f = (freqSm * ratio).clip(40, 12000);
        f = (f * (1 + (SinOsc.kr(fmRateSm) * fmSm))).clip(40, 12000);
        aFollow = curve.linlin(0, 1, 0.12, 1.0);

        sig = Formant.ar(f, f * 1.5, f * 2.5) * 0.6;
        extra1 = (SinOsc.ar(f) * 0.25) + (VarSaw.ar(f * 0.5, 0, 0.2) * 0.15);
        sig = sig + (extra1 * toneSm);
        sig = RLPF.ar(sig, (f * (1 + resSm * 2)).clip(200, 8000), resQSm);
        sig = HPF.ar(sig, hpSm);
        sig = LPF.ar(sig, lpSm);
        sig = tanh(sig * (1 + (gritSm * 6)));

        outSig = Pan2.ar(sig * aFollow, pan);
        outSig = LeakDC.ar(outSig);
        outSig = HPF.ar(outSig, 20);

        outSig = outSig * ampSm * env;
        outSig = Limiter.ar(outSig, 0.98);

        Out.ar(outDry,  outSig * drySm);
        Out.ar(outSend, outSig * sendSm);
    }).add;

    // ---------------- SIREN 3 (BENIDUB BIP BIP) ----------------
    SynthDef(\benidubBip, { |
        outDry=0, outSend=0,
        dryLevel=0.045, sendLevel=0.11,
        amp=1.0,

        freq=1200, freqLag=0.08,
        freqMin=500, freqMax=5000,

        rate=4.0, rateLag=0.10,
        rateMin=0.5, rateMax=12.0,

        tone=0.25, toneLag=0.10,   // 0..1 sine->buzzy
        drive=0.15, driveLag=0.10, // 0..1 punch

        bipAtk=0.0018, bipRel=0.040,
        glide=0.010,                // pitch glide per tone-step
        gateAtk=0.012, gateRel=0.20,
        pan=0.0, gate=1
    |
        var gEnv, fSm, rSm, tSm, dSm;
        var ampSm, drySm, sendSm;
        var trig, env;
        var which, f2, fSel, fGlide;
        var sine, body, sig, outSig;
        var driveAmt;

        gEnv = EnvGen.ar(Env.asr(gateAtk, 1.0, gateRel), gate, doneAction:2);

        ampSm  = Lag.kr(amp, 0.02);
        drySm  = Lag.kr(dryLevel, 0.02);
        sendSm = Lag.kr(sendLevel, 0.02);

        fSm = VarLag.kr(freq.clip(freqMin, freqMax), freqLag.clip(0.0, 2.0), warp:\exp);
        rSm = VarLag.kr(rate.clip(rateMin, rateMax), rateLag.clip(0.0, 2.0), warp:\exp);
        tSm = VarLag.kr(tone.clip(0.0, 1.0), toneLag.clip(0.0, 2.0), warp:\lin);
        dSm = VarLag.kr(drive.clip(0.0, 1.0), driveLag.clip(0.0, 2.0), warp:\lin);

        // alternating two-tone, classic feel
        which = LFPulse.kr(rSm, 0, 0.5);
        f2 = (fSm * 0.82).clip(freqMin, freqMax); // second tone slightly lower
        fSel = Select.kr(which, [fSm, f2]);

        // tiny pitch glide => "benidub" vibe (not robotic)
        fGlide = Lag.kr(fSel, glide.clip(0.0, 0.05));

        trig = Impulse.kr(rSm);
        env = EnvGen.ar(Env.perc(bipAtk.clip(0.001, 0.02), bipRel.clip(0.01, 0.2), curve: -4), trig);

        // core: sine + a bit of buzzy body
        sine = SinOsc.ar(fGlide, 0, 0.95);
        body = (VarSaw.ar(fGlide, 0, 0.25) * 0.35) + (Pulse.ar(fGlide * 0.5, 0.5) * 0.12);
        sig = XFade2.ar(sine, body, (tSm * 2 - 1)); // 0->sine, 1->body-ish

        // mild drive
        driveAmt = (1 + (dSm * 10));
        sig = tanh(sig * driveAmt) * (1 / (1 + dSm * 2));

        sig = sig * env;
        sig = LeakDC.ar(sig);
        sig = HPF.ar(sig, 60);
        sig = LPF.ar(sig, (fGlide * 7).clip(1500, 12000));

        outSig = Pan2.ar(sig, pan);
        outSig = outSig * ampSm * gEnv;
        outSig = Limiter.ar(outSig, 0.98);

        Out.ar(outDry,  outSig * drySm);
        Out.ar(outSend, outSig * sendSm);
    }).add;

    s.sync;

    // start master + delay
    ~masterVol = 0.25;
    ~master = Synth(\masterOut, [\inbus, ~masterBus, \out, 0, \vol, ~masterVol, \volLag, 0.002]);
    ~delay  = Synth(\dubDelay,  [\inbus, ~fxBus, \out, ~masterBus, \mix, 1.0, \level, 1.0]);

    ~delayTime = 0.33;
    ~fb = 0.55;

    ~applyTime = { |t| ~delayTime = t.clip(0.03, 2.0); ~delay.set(\time, ~delayTime); };
    ~applyFb   = { |x| ~fb = x.clip(0.0, 0.92); ~delay.set(\fb, ~fb); };
    ~applyMaster = { |v| ~masterVol = v.clip(0.0, 1.0); ~master.set(\vol, ~masterVol); };

    ~applyTime.(~delayTime);
    ~applyFb.(~fb);
    ~applyMaster.(~masterVol);

    // -------- state: siren1
    ~siren = nil;
    ~sirenFreqMin = 500.0;  ~sirenFreqMax = 5000.0;  ~sirenFreq = 1000.0;
    ~sirenRateMin = 0.05;   ~sirenRateMax = 5.0;     ~sirenRate = 0.6;
    ~sirenDepth = 0.55;

    ~setSirenFreq = { |hz| ~sirenFreq = hz.clip(~sirenFreqMin, ~sirenFreqMax); if(~siren.notNil){~siren.set(\freq,~sirenFreq)}; };
    ~setSirenRate = { |r|  ~sirenRate = r.clip(~sirenRateMin, ~sirenRateMax); if(~siren.notNil){~siren.set(\rate,~sirenRate)}; };
    ~setSirenDepth= { |d|  ~sirenDepth= d.clip(0,1); if(~siren.notNil){~siren.set(\depth,~sirenDepth)}; };

    ~startSiren = {
        ~siren.tryPerform(\free);
        ~siren = Synth(\dubSiren_immediate, [
            \freq, ~sirenFreq, \freqMin, ~sirenFreqMin, \freqMax, ~sirenFreqMax,
            \rate, ~sirenRate, \rateMin, ~sirenRateMin, \rateMax, ~sirenRateMax,
            \depth, ~sirenDepth,
            \outDry, ~masterBus, \outSend, ~fxBus
        ], target: s.defaultGroup);
        "[SC] siren1 start".postln;
    };
    ~stopSiren = { if(~siren.notNil){ ~siren.set(\gate,0); ~siren=nil; "[SC] siren1 stop".postln; } };
    ~toggleSiren = { if(~siren.isNil){ ~startSiren.() }{ ~stopSiren.() } };

    // -------- state: air
    ~air = nil;
    ~airFreqMin = 200.0;  ~airFreqMax = 2000.0;  ~airFreq = 450.0;
    ~airRateMin = 0.05;   ~airRateMax = 1.5;     ~airRate = 0.18;
    ~airDepth = 0.60;

    ~applyAir = { if(~air.notNil){ ~air.set(\freq,~airFreq,\rate,~airRate,\depth,~airDepth); }; };
    ~setAirFreq = { |hz| ~airFreq = hz.clip(~airFreqMin, ~airFreqMax); ~applyAir.(); };
    ~setAirRate = { |r|  ~airRate = r.clip(~airRateMin, ~airRateMax);  ~applyAir.(); };
    ~setAirDepth= { |d|  ~airDepth= d.clip(0,1); ~applyAir.(); };

    ~startAir = {
        ~air.tryPerform(\free);
        ~air = Synth(\airRaidSiren, [
            \freq, ~airFreq, \freqMin, ~airFreqMin, \freqMax, ~airFreqMax,
            \rate, ~airRate, \rateMin, ~airRateMin, \rateMax, ~airRateMax,
            \depth, ~airDepth,
            \outDry, ~masterBus, \outSend, ~fxBus
        ], target: s.defaultGroup);
        "[SC] air start".postln;
    };
    ~stopAir = { if(~air.notNil){ ~air.set(\gate,0); ~air=nil; "[SC] air stop".postln; } };
    ~toggleAir = { if(~air.isNil){ ~startAir.() }{ ~stopAir.() } };

    // -------- state: benidub bip
    ~bens = nil;
    ~bensFreqMin = 500.0;  ~bensFreqMax = 5000.0;  ~bensFreq = 1200.0;
    ~bensRateMin = 0.5;    ~bensRateMax = 12.0;    ~bensRate = 4.0;
    ~bensTone = 0.25;
    ~bensDrive = 0.15;

    ~applyBens = {
        if(~bens.notNil) { ~bens.set(\freq,~bensFreq,\rate,~bensRate,\tone,~bensTone,\drive,~bensDrive); };
    };
    ~setBensFreq = { |hz| ~bensFreq = hz.clip(~bensFreqMin, ~bensFreqMax); ~applyBens.(); };
    ~setBensRate = { |r|  ~bensRate = r.clip(~bensRateMin, ~bensRateMax);  ~applyBens.(); };
    ~setBensTone = { |x|  ~bensTone = x.clip(0,1); ~applyBens.(); };
    ~setBensDrive= { |x|  ~bensDrive= x.clip(0,1); ~applyBens.(); };

    ~startBens = {
        ~bens.tryPerform(\free);
        ~bens = Synth(\benidubBip, [
            \freq, ~bensFreq, \freqMin, ~bensFreqMin, \freqMax, ~bensFreqMax,
            \rate, ~bensRate, \rateMin, ~bensRateMin, \rateMax, ~bensRateMax,
            \tone, ~bensTone, \drive, ~bensDrive,
            \outDry, ~masterBus, \outSend, ~fxBus
        ], target: s.defaultGroup);
        "[SC] bens start".postln;
    };
    ~stopBens = { if(~bens.notNil){ ~bens.set(\gate,0); ~bens=nil; "[SC] bens stop".postln; } };
    ~toggleBens = { if(~bens.isNil){ ~startBens.() }{ ~stopBens.() } };

    // ---------------- OSC ----------------
    OSCdef(\timeSet, { |m| ~applyTime.(m[1].asFloat) }, "/delay/time", recvPort: ~oscPort);
    OSCdef(\fbSet,   { |m| ~applyFb.(m[1].asFloat) },   "/delay/fb",   recvPort: ~oscPort);
    OSCdef(\clear, { |m|
        ~delay.set(\clear, 1);
        SystemClock.sched(0.07, { ~delay.set(\clear, 0); nil });
    }, "/delay/clear", recvPort: ~oscPort);

    OSCdef(\masterVol, { |m| ~applyMaster.(m[1].asFloat) }, "/master/vol", recvPort: ~oscPort);

    OSCdef(\sirenToggle, { |m| ~toggleSiren.() }, "/siren/toggle", recvPort: ~oscPort);
    OSCdef(\sirenStop,   { |m| ~stopSiren.() },   "/siren/stop",   recvPort: ~oscPort);
    OSCdef(\sirenFreq,   { |m| ~setSirenFreq.(m[1].asFloat) },  "/siren/freq",  recvPort: ~oscPort);
    OSCdef(\sirenRate,   { |m| ~setSirenRate.(m[1].asFloat) },  "/siren/rate",  recvPort: ~oscPort);
    OSCdef(\sirenDepth,  { |m| ~setSirenDepth.(m[1].asFloat) }, "/siren/depth", recvPort: ~oscPort);

    OSCdef(\airToggle, { |m| ~toggleAir.() }, "/air/toggle", recvPort: ~oscPort);
    OSCdef(\airStop,   { |m| ~stopAir.() },   "/air/stop",   recvPort: ~oscPort);
    OSCdef(\airFreq,   { |m| ~setAirFreq.(m[1].asFloat) },   "/air/freq",  recvPort: ~oscPort);
    OSCdef(\airRate,   { |m| ~setAirRate.(m[1].asFloat) },   "/air/rate",  recvPort: ~oscPort);
    OSCdef(\airDepth,  { |m| ~setAirDepth.(m[1].asFloat) },  "/air/depth", recvPort: ~oscPort);

    // benidub bip
    OSCdef(\bensToggle, { |m| ~toggleBens.() }, "/bens/toggle", recvPort: ~oscPort);
    OSCdef(\bensStop,   { |m| ~stopBens.() },   "/bens/stop",   recvPort: ~oscPort);
    OSCdef(\bensFreq,   { |m| ~setBensFreq.(m[1].asFloat) },   "/bens/freq",  recvPort: ~oscPort);
    OSCdef(\bensRate,   { |m| ~setBensRate.(m[1].asFloat) },   "/bens/rate",  recvPort: ~oscPort);
    OSCdef(\bensTone,   { |m| ~setBensTone.(m[1].asFloat) },   "/bens/tone",  recvPort: ~oscPort);
    OSCdef(\bensDrive,  { |m| ~setBensDrive.(m[1].asFloat) },  "/bens/drive", recvPort: ~oscPort);

    "[SC] READY".postln;
});
)
