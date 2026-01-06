# Python SCRIPT (SMALL UI) + TAP TEMPO + TRUE x2 (DOUBLES/HALVES THE ACTUAL DELAY SLIDER) + 3 SIRENS
# ONE shared PITCH slider for all 3 (each with its own Hz range)
# ONE shared RATE  slider for all 3 (each with its own rate range)

from pythonosc.udp_client import SimpleUDPClient
import tkinter as tk
import time
from collections import deque

SC_IP = "127.0.0.1"
SC_PORT = 57120
c = SimpleUDPClient(SC_IP, SC_PORT)

TIME_STEP = 0.02
FB_STEP = 0.03
VOL_STEP = 0.05

TIME_MIN, TIME_MAX = 0.03, 2.0
FB_MIN, FB_MAX = 0.0, 0.92
VOL_MIN, VOL_MAX = 0.0, 1.0

# Per-siren pitch ranges
S1_HZ_MIN, S1_HZ_MAX = 500.0, 5000.0
BENS_HZ_MIN, BENS_HZ_MAX = 500.0, 5000.0
AIR_HZ_MIN, AIR_HZ_MAX = 200.0, 2000.0

# Per-siren rate ranges
S1_RATE_MIN, S1_RATE_MAX = 0.05, 5.0
BENS_RATE_MIN, BENS_RATE_MAX = 0.5, 12.0
AIR_RATE_MIN, AIR_RATE_MAX = 0.05, 1.5

SEND_HZ = 120.0
SEND_DT = 1.0 / SEND_HZ

# smoothing (audio-safe)
DELAY_ALPHA = 0.06
FB_ALPHA = 0.06

PITCH_ALPHA = 0.10
RATE_ALPHA  = 0.12

S1_DEPTH_ALPHA = 0.10
AIR_DEPTH_ALPHA = 0.10

BENS_TONE_ALPHA  = 0.12
BENS_DRIVE_ALPHA = 0.12


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def exp_map_0_1(x01: float, vmin: float, vmax: float) -> float:
    x01 = clamp(x01, 0.0, 1.0)
    ratio = vmax / vmin
    return vmin * (ratio ** x01)


# --- tap tempo state ---
tap_times = deque(maxlen=8)
tap_intervals = deque(maxlen=6)

bpm_var = None
tap_hint_var = None


def _update_bpm_display(delay_time: float, x2_on: bool):
    bpm = 60.0 / delay_time if delay_time > 1e-9 else 0.0
    bpm_var.set(f"{bpm:5.1f} bpm")
    tap_hint_var.set(f"{delay_time:0.3f}s {'x2' if x2_on else ''}".strip())


# --- OSC actions ---
def clear_delay():
    c.send_message("/delay/clear", 1)

def siren1_toggle():
    c.send_message("/siren/toggle", 1)

def siren1_stop():
    c.send_message("/siren/stop", 1)

def air_toggle():
    c.send_message("/air/toggle", 1)

def air_stop():
    c.send_message("/air/stop", 1)

def bens_toggle():
    c.send_message("/bens/toggle", 1)

def bens_stop():
    c.send_message("/bens/stop", 1)


# --- GUI (compact) ---
root = tk.Tk()
root.title("Delay + Vol + 3 Sirens (shared pitch/rate)")
root.focus_force()
root.option_add("*Font", "TkDefaultFont 10")

outer = tk.Frame(root, padx=8, pady=6)
outer.pack(fill="both", expand=True)

tk.Label(
    outer,
    text="←/→ delay  ↑/↓ fb  [/] vol  t tap  2 x2  s/x dub  a/z air  b/n bip  Esc clear",
    anchor="w",
    justify="left"
).pack(fill="x", pady=(0, 4))

tap_row = tk.Frame(outer)
tap_row.pack(fill="x", pady=(0, 4))

bpm_var = tk.StringVar(value="— bpm")
tap_hint_var = tk.StringVar(value="tap (t)")

tk.Label(tap_row, text="Tap:", width=4, anchor="w").pack(side="left")
tk.Label(tap_row, textvariable=tap_hint_var, width=12, anchor="w").pack(side="left", padx=(0, 8))
tk.Label(tap_row, text="BPM:", width=4, anchor="w").pack(side="left")
tk.Label(tap_row, textvariable=bpm_var, width=10, anchor="w").pack(side="left", padx=(0, 8))

x2_var = tk.IntVar(value=0)

knob = tk.Frame(outer)
knob.pack(fill="both", expand=True)

SLIDER_LEN = 250
SLIDER_HANDLE = 14


def make_scale(label, frm, to, cmd, from_=0.0, res=0.001):
    sc = tk.Scale(
        frm, from_=from_, to=to, resolution=res,
        orient="horizontal", length=SLIDER_LEN,
        sliderlength=SLIDER_HANDLE,
        label=label, command=cmd
    )
    sc.pack(fill="x", pady=(2, 0))
    return sc


# --- targets + smoothed ---
delay_time_target = 0.33
delay_time_sm = delay_time_target

fb_target = 0.55
fb_sm = fb_target

vol_target = 0.25

pitch01_target = 0.55
rate01_target  = 0.45
pitch01_sm = pitch01_target
rate01_sm  = rate01_target

# extras
s1_depth_target = 0.55
air_depth_target = 0.60
bens_tone_target = 0.25
bens_drive_target = 0.15

s1_depth_sm = s1_depth_target
air_depth_sm = air_depth_target
bens_tone_sm = bens_tone_target
bens_drive_sm = bens_drive_target


# --- slider callbacks ---
def on_delay_time_slider(v):
    global delay_time_target
    delay_time_target = clamp(float(v), TIME_MIN, TIME_MAX)
    _update_bpm_display(delay_time_target, x2_var.get() == 1)

def on_fb_slider(v):
    global fb_target
    fb_target = clamp(float(v), FB_MIN, FB_MAX)

def on_vol_slider(v):
    global vol_target
    vol_target = clamp(float(v), VOL_MIN, VOL_MAX)

def on_pitch(v):
    global pitch01_target
    pitch01_target = clamp(float(v), 0.0, 1.0)

def on_rate(v):
    global rate01_target
    rate01_target = clamp(float(v), 0.0, 1.0)

def on_s1_depth(v):
    global s1_depth_target
    s1_depth_target = clamp(float(v), 0.0, 1.0)

def on_air_depth(v):
    global air_depth_target
    air_depth_target = clamp(float(v), 0.0, 1.0)

def on_bens_tone(v):
    global bens_tone_target
    bens_tone_target = clamp(float(v), 0.0, 1.0)

def on_bens_drive(v):
    global bens_drive_target
    bens_drive_target = clamp(float(v), 0.0, 1.0)


# --- build sliders ---
delay_time_slider = make_scale(
    "Delay TIME (sec) [tap]  (x2 doubles/halves THIS value)",
    knob, TIME_MAX, on_delay_time_slider, from_=TIME_MIN, res=0.001
)
delay_time_slider.set(delay_time_target)

fb_slider = make_scale("Feedback", knob, FB_MAX, on_fb_slider, from_=FB_MIN, res=0.001)
fb_slider.set(fb_target)

vol_slider = make_scale("Master Vol", knob, VOL_MAX, on_vol_slider, from_=VOL_MIN, res=0.001)
vol_slider.set(vol_target)

pitch_slider = make_scale("PITCH (all): dub/ben 500..5000, air 200..2000", knob, 1.0, on_pitch, from_=0.0, res=0.001)
pitch_slider.set(pitch01_target)

rate_slider = make_scale("RATE (all): dub 0.05..5, ben 0.5..12, air 0.05..1.5", knob, 1.0, on_rate, from_=0.0, res=0.001)
rate_slider.set(rate01_target)

tk.Label(knob, text="Extras", anchor="w").pack(fill="x", pady=(6, 0))
s1d = make_scale("Dub Depth", knob, 1.0, on_s1_depth, from_=0.0, res=0.001); s1d.set(s1_depth_target)
ad  = make_scale("Air Depth", knob, 1.0, on_air_depth, from_=0.0, res=0.001); ad.set(air_depth_target)
bt  = make_scale("Ben Tone",  knob, 1.0, on_bens_tone, from_=0.0, res=0.001); bt.set(bens_tone_target)
bd  = make_scale("Ben Drive", knob, 1.0, on_bens_drive, from_=0.0, res=0.001); bd.set(bens_drive_target)


# --- x2 that actually doubles/halves the delay slider ---
_last_x2 = 0

def apply_x2_from_checkbox():
    """
    Called when checkbox changes.
    If it turned ON: multiply delay time by 2
    If it turned OFF: divide delay time by 2
    """
    global delay_time_target, _last_x2

    new_x2 = x2_var.get()
    if new_x2 == _last_x2:
        return

    if new_x2 == 1:
        delay_time_target = clamp(delay_time_target * 2.0, TIME_MIN, TIME_MAX)
    else:
        delay_time_target = clamp(delay_time_target * 0.5, TIME_MIN, TIME_MAX)

    _last_x2 = new_x2
    delay_time_slider.set(delay_time_target)  # makes it feel like you dragged it
    _update_bpm_display(delay_time_target, x2_var.get() == 1)

def toggle_x2_key():
    """Key '2' flips the checkbox, then checkbox handler does the doubling."""
    x2_var.set(0 if x2_var.get() else 1)
    apply_x2_from_checkbox()


tk.Checkbutton(
    tap_row,
    text="x2",
    variable=x2_var,
    command=apply_x2_from_checkbox
).pack(side="left")

_update_bpm_display(delay_time_target, x2_var.get() == 1)


# --- key helpers ---
def time_down():
    global delay_time_target
    delay_time_target = clamp(delay_time_target - TIME_STEP, TIME_MIN, TIME_MAX)
    delay_time_slider.set(delay_time_target)
    _update_bpm_display(delay_time_target, x2_var.get() == 1)

def time_up():
    global delay_time_target
    delay_time_target = clamp(delay_time_target + TIME_STEP, TIME_MIN, TIME_MAX)
    delay_time_slider.set(delay_time_target)
    _update_bpm_display(delay_time_target, x2_var.get() == 1)

def fb_down():
    global fb_target
    fb_target = clamp(fb_target - FB_STEP, FB_MIN, FB_MAX)
    fb_slider.set(fb_target)

def fb_up():
    global fb_target
    fb_target = clamp(fb_target + FB_STEP, FB_MIN, FB_MAX)
    fb_slider.set(fb_target)

def vol_down():
    global vol_target
    vol_target = clamp(vol_target - VOL_STEP, VOL_MIN, VOL_MAX)
    vol_slider.set(vol_target)

def vol_up():
    global vol_target
    vol_target = clamp(vol_target + VOL_STEP, VOL_MIN, VOL_MAX)
    vol_slider.set(vol_target)

def tap_tempo():
    """Tap sets the ACTUAL delay time."""
    global delay_time_target
    now = time.time()
    tap_times.append(now)
    if len(tap_times) < 2:
        tap_hint_var.set("tap…")
        return
    dt = tap_times[-1] - tap_times[-2]
    if dt < 0.08 or dt > 2.5:
        tap_intervals.clear()
        tap_hint_var.set("reset")
        return
    tap_intervals.append(dt)
    if len(tap_intervals) < 2:
        tap_hint_var.set("…")
        return

    sdt = sorted(tap_intervals)
    mid = len(sdt) // 2
    est = sdt[mid] if (len(sdt) % 2 == 1) else 0.5 * (sdt[mid - 1] + sdt[mid])
    est = clamp(est, TIME_MIN, TIME_MAX)

    delay_time_target = est
    delay_time_slider.set(delay_time_target)
    _update_bpm_display(delay_time_target, x2_var.get() == 1)


# --- sending ---
last_send = 0.0
last_sent = {}

def maybe_send(addr, val, eps):
    old = last_sent.get(addr, None)
    if old is None or abs(val - old) > eps:
        c.send_message(addr, float(val))
        last_sent[addr] = val


def tick():
    global delay_time_sm, fb_sm, last_send
    global pitch01_sm, rate01_sm
    global s1_depth_sm, air_depth_sm, bens_tone_sm, bens_drive_sm

    now = time.time()
    if now - last_send >= SEND_DT:
        last_send = now

        delay_time_sm = delay_time_sm + DELAY_ALPHA * (delay_time_target - delay_time_sm)
        delay_time_sm = clamp(delay_time_sm, TIME_MIN, TIME_MAX)

        fb_sm = fb_sm + FB_ALPHA * (fb_target - fb_sm)
        fb_sm = clamp(fb_sm, FB_MIN, FB_MAX)

        vol_now = clamp(vol_target, VOL_MIN, VOL_MAX)

        pitch01_sm = pitch01_sm + PITCH_ALPHA * (pitch01_target - pitch01_sm)
        rate01_sm  = rate01_sm  + RATE_ALPHA  * (rate01_target  - rate01_sm)

        # pitch per siren
        s1_hz   = exp_map_0_1(pitch01_sm, S1_HZ_MIN,   S1_HZ_MAX)
        bens_hz = exp_map_0_1(pitch01_sm, BENS_HZ_MIN, BENS_HZ_MAX)
        air_hz  = exp_map_0_1(pitch01_sm, AIR_HZ_MIN,  AIR_HZ_MAX)

        # rate per siren
        s1_rate   = exp_map_0_1(rate01_sm, S1_RATE_MIN,   S1_RATE_MAX)
        bens_rate = exp_map_0_1(rate01_sm, BENS_RATE_MIN, BENS_RATE_MAX)
        air_rate  = exp_map_0_1(rate01_sm, AIR_RATE_MIN,  AIR_RATE_MAX)

        # extras smoothing
        s1_depth_sm   = s1_depth_sm   + S1_DEPTH_ALPHA    * (s1_depth_target  - s1_depth_sm)
        air_depth_sm  = air_depth_sm  + AIR_DEPTH_ALPHA   * (air_depth_target - air_depth_sm)
        bens_tone_sm  = bens_tone_sm  + BENS_TONE_ALPHA   * (bens_tone_target - bens_tone_sm)
        bens_drive_sm = bens_drive_sm + BENS_DRIVE_ALPHA  * (bens_drive_target - bens_drive_sm)

        s1_depth   = clamp(s1_depth_sm, 0, 1)
        air_depth  = clamp(air_depth_sm, 0, 1)
        bens_tone  = clamp(bens_tone_sm, 0, 1)
        bens_drive = clamp(bens_drive_sm, 0, 1)

        maybe_send("/delay/time", delay_time_sm, 0.0005)
        maybe_send("/delay/fb",   fb_sm,         0.0005)
        maybe_send("/master/vol", vol_now,       0.0005)

        maybe_send("/siren/freq",  s1_hz,    1.0)
        maybe_send("/siren/rate",  s1_rate,  0.01)
        maybe_send("/siren/depth", s1_depth, 0.003)

        maybe_send("/air/freq",  air_hz,    0.7)
        maybe_send("/air/rate",  air_rate,  0.005)
        maybe_send("/air/depth", air_depth, 0.003)

        maybe_send("/bens/freq",  bens_hz,    1.0)
        maybe_send("/bens/rate",  bens_rate,  0.01)
        maybe_send("/bens/tone",  bens_tone,  0.003)
        maybe_send("/bens/drive", bens_drive, 0.003)

    root.after(5, tick)

root.after(5, tick)

# --- key bindings ---
root.bind("<Left>",   lambda e: time_down())
root.bind("<Right>",  lambda e: time_up())
root.bind("<Down>",   lambda e: fb_down())
root.bind("<Up>",     lambda e: fb_up())
root.bind("<Escape>", lambda e: clear_delay())

root.bind("[",        lambda e: vol_down())
root.bind("]",        lambda e: vol_up())

root.bind("t",        lambda e: tap_tempo())
root.bind("T",        lambda e: tap_tempo())

root.bind("2",        lambda e: toggle_x2_key())

root.bind("s",        lambda e: siren1_toggle())
root.bind("S",        lambda e: siren1_toggle())
root.bind("x",        lambda e: siren1_stop())
root.bind("X",        lambda e: siren1_stop())

root.bind("a",        lambda e: air_toggle())
root.bind("A",        lambda e: air_toggle())
root.bind("z",        lambda e: air_stop())
root.bind("Z",        lambda e: air_stop())

root.bind("b",        lambda e: bens_toggle())
root.bind("B",        lambda e: bens_toggle())
root.bind("n",        lambda e: bens_stop())
root.bind("N",        lambda e: bens_stop())

root.mainloop()
