from gpiozero import Button
from signal import pause
import pygame
import time
import os

# Mappa GPIO -> file audio (modifica i nomi se vuoi)
BUTTON_SOUNDS = {
    17: "sample1.wav",
    27: "sample2.wav",
    22: "sample3.wav",
    5:  "sample4.wav",
    6:  "sample5.wav",
    13: "sample6.wav",
}

# Impostazioni
DEBOUNCE_SECONDS = 0.15   # antirimbalzo software
MIXER_FREQ = 44100        # 44.1 kHz
MIXER_CHANNELS = 2        # stereo
MIXER_BUFFER = 512        # buffer piccolo per latenza bassa

# --- Init audio ---
pygame.mixer.pre_init(frequency=MIXER_FREQ, size=-16, channels=MIXER_CHANNELS, buffer=MIXER_BUFFER)
pygame.init()
pygame.mixer.set_num_channels(len(BUTTON_SOUNDS))  # un canale per bottone

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

def on_press(pin):
    now = time.time()
    # antirimbalzo semplice
    if now - last_press_time.get(pin, 0) < DEBOUNCE_SECONDS:
        return
    last_press_time[pin] = now

    ch = channels[pin]
    snd = sounds[pin]

    # Riproduci (ferma il canale se vuoi evitare overlap sullo STESSO canale)
    # ch.stop()
    ch.play(snd)

    print(f"▶️ GPIO {pin} -> {os.path.basename(snd.get_raw().__class__.__name__ if hasattr(snd,'get_raw') else 'audio')} (file: {snd})")

for pin in BUTTON_SOUNDS.keys():
    # pull-up interna; quando premi il pulsante verso GND, l’evento è "pressed"
    btn = Button(pin, pull_up=True, bounce_time=DEBOUNCE_SECONDS)
    btn.when_pressed = (lambda p: (lambda: on_press(p)))(pin)
    buttons[pin] = btn
    last_press_time[pin] = 0.0

print("Pronto! Premi i pulsanti per riprodurre i suoni. Ctrl+C per uscire.")
try:
    pause()  # resta in attesa di eventi
except KeyboardInterrupt:
    print("\nUscita.")
finally:
    pygame.quit()
