from gpiozero import Button
from pythonosc.udp_client import SimpleUDPClient
from signal import pause
import time

# === Mappa: GPIO -> campione (SuperCollider usa questi pin come chiavi) ===
BUTTON_PINS = [17, 27, 22]  # stessi pin usati nei buffer SC

# === Controlli ===
PAUSE_PIN = 5   # pin fisico 29
STOP_PIN  = 6   # pin fisico 31

DEBOUNCE_SECONDS = 0.15

# OSC verso sclang (gli OSCdef vivono su 57120)
client = SimpleUDPClient("127.0.0.1", 57120)

# Stato pausa per toggle
is_paused = False
last_press_time = {}

def debounce_ok(pin):
    now = time.time()
    if now - last_press_time.get(pin, 0) < DEBOUNCE_SECONDS:
        return False
    last_press_time[pin] = now
    return True

def on_sample(pin):
    if not debounce_ok(pin):
        return
    # invia /play con il numero del pin (SuperCollider userà ~bufs[pin])
    client.send_message("/play", [pin])
    print(f"▶️ PLAY request from GPIO {pin}")

def on_pause():
    global is_paused
    if not debounce_ok(PAUSE_PIN):
        return
    if is_paused:
        client.send_message("/resume", [])
        is_paused = False
        print("⏯️ RESUME")
    else:
        client.send_message("/pause", [])
        is_paused = True
        print("⏸️ PAUSE")

def on_stop():
    if not debounce_ok(STOP_PIN):
        return
    client.send_message("/stop", [])
    print("⏹️ STOP")

# --- Wiring: un capo del pulsante a GPIO, l’altro a GND (pull-up interna) ---
buttons = []
for pin in BUTTON_PINS:
    btn = Button(pin, pull_up=True, bounce_time=DEBOUNCE_SECONDS)
    btn.when_pressed = (lambda p: (lambda: on_sample(p)))(pin)
    buttons.append(btn)
    last_press_time[pin] = 0.0

btn_pause = Button(PAUSE_PIN, pull_up=True, bounce_time=DEBOUNCE_SECONDS)
btn_stop  = Button(STOP_PIN,  pull_up=True, bounce_time=DEBOUNCE_SECONDS)
btn_pause.when_pressed = on_pause
btn_stop.when_pressed  = on_stop
last_press_time[PAUSE_PIN] = 0.0
last_press_time[STOP_PIN]  = 0.0

print("GPIO→OSC ready. Press buttons! Ctrl+C to quit.")
try:
    pause()
except KeyboardInterrupt:
    print("\nBye.")
