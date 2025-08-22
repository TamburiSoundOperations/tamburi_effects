from gpiozero import Button
from signal import pause
import pygame
import time
import os

# --- Mappa GPIO -> file audio (puoi modificare i nomi/file) ---
BUTTON_SOUNDS = {
    17: "sounds/Jah Shaka - Jah Shaka answers - 01 1.wav",
    27: "sounds/Jah Shaka - Jah Shaka answers - 02 2.wav",
    22: "sounds/Jah Shaka - Jah Shaka answers - 03 3.wav",
}

# --- Controlli di trasporto ---
# Pin fisico 29 -> GPIO 5 (PAUSA/RIPRENDI)
# Pin fisico 31 -> GPIO 6 (STOP)
PAUSE_PIN = 5
STOP_PIN  = 6

# Impostazioni
DEBOUNCE_SECONDS = 0.15   # antirimbalzo software
MIXER_FREQ = 44100        # 44.1 kHz
MIXER_CHANNELS = 2        # stereo
MIXER_BUFFER = 512        # buffer piccolo per latenza bassa

# --- Init audio ---
pygame.mixer.pre_init(frequency=MIXER_FREQ, size=-16, channels=MIXER_CHANNELS, buffer=MIXER_BUFFER)
pygame.init()
pygame.mixer.set_num_channels(len(BUTTON_SOUNDS))  # un canale per bottone
is_paused = False  # stato pausa globale

# Carica i suoni
sounds = {}
channels = {}
for idx, (pin, fname) in enumerate(BUTTON_SOUNDS.items()):
    if not os.path.exists(fname):
        raise FileNotFoundError(f"File audio mancante: {fname}")
    sounds[pin] = pygame.mixer.Sound(fname)
    channels[pin] = pygame.mixer.Channel(idx)  # canale dedicato (consente sovrapposizione tra pulsanti)
    channels[pin].set_volume(1.0)

# --- Init GPIO (pull-up interna, attivo-basso verso GND) ---
buttons = {}
last_press_time = {}

def debounce_ok(pin):
    now = time.time()
    if now - last_press_time.get(pin, 0) < DEBOUNCE_SECONDS:
        return False
    last_press_time[pin] = now
    return True

def on_press(pin):
    global is_paused
    if not debounce_ok(pin):
        return

    # Se siamo in pausa, prima riprendi
    if is_paused:
        pygame.mixer.unpause()
        is_paused = False
        print("⏯️ RESUME (tutti i canali)")

    ch = channels[pin]
    snd = sounds[pin]

    # Per evitare overlap sullo STESSO canale, scommenta la riga sotto
    # ch.stop()

    ch.play(snd)
    print(f"▶️ PLAY GPIO {pin} -> {os.path.basename(fname) if (fname:=snd) else 'audio'}")

def on_pause_press():
    global is_paused
    if not debounce_ok(PAUSE_PIN):
        return
    if is_paused:
        pygame.mixer.unpause()
        is_paused = False
        print("⏯️ RESUME (tutti i canali)")
    else:
        pygame.mixer.pause()
        is_paused = True
        print("⏸️ PAUSE (tutti i canali)")

def on_stop_press():
    global is_paused
    if not debounce_ok(STOP_PIN):
        return
    pygame.mixer.stop()
    is_paused = False
    print("⏹️ STOP (tutti i canali)")

# Pulsanti sample
for pin in BUTTON_SOUNDS.keys():
    btn = Button(pin, pull_up=True, bounce_time=DEBOUNCE_SECONDS)
    btn.when_pressed = (lambda p: (lambda: on_press(p)))(pin)
    buttons[pin] = btn
    last_press_time[pin] = 0.0

# Pulsanti pausa/stop
btn_pause = Button(PAUSE_PIN, pull_up=True, bounce_time=DEBOUNCE_SECONDS)
btn_stop  = Button(STOP_PIN,  pull_up=True, bounce_time=DEBOUNCE_SECONDS)
btn_pause.when_pressed = on_pause_press
btn_stop.when_pressed  = on_stop_press
last_press_time[PAUSE_PIN] = 0.0
last_press_time[STOP_PIN]  = 0.0

print("Pronto!\n- 3 pulsanti: riproducono i sample\n- Pin fisico 29 (GPIO5): PAUSA/RIPRENDI\n- Pin fisico 31 (GPIO6): STOP\nCtrl+C per uscire.")
try:
    pause()  # resta in attesa di eventi
except KeyboardInterrupt:
    print("\nUscita.")
finally:
    pygame.quit()
