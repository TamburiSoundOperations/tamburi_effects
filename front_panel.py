from pynput import keyboard
from pythonosc import udp_client

# Set up the OSC client
client = udp_client.SimpleUDPClient("127.0.0.1", 4559)

# Initialize parameters
params = {
    "pitch": 60,            # Default MIDI pitch
    "rate": 1.0,            # Default rate
    "delay_time": 0.5,      # Default delay time
    "delay_feedback": 0.5,  # Default delay feedback
    "echo_phase": 0.25,     # Default echo phase
    "echo_decay": 2.0       # Default echo decay
}

# Parameter adjustment step sizes
steps = {
    "pitch": 1,
    "rate": 0.1,
    "delay_time": 0.1,
    "delay_feedback": 0.1,
    "echo_phase": 0.05,
    "echo_decay": 0.1
}

# Function to send updated parameters via OSC
def send_osc(parameter):
    client.send_message(f"/osc/{parameter}", params[parameter])
    print(f"Updated {parameter}: {params[parameter]}")

# Key handling
def on_press(key):
    try:
        if key.char == 'q':  # Increase pitch
            params["pitch"] += steps["pitch"]
            send_osc("pitch")
        elif key.char == 'a':  # Decrease pitch
            params["pitch"] -= steps["pitch"]
            send_osc("pitch")
        elif key.char == 'w':  # Increase rate
            params["rate"] += steps["rate"]
            send_osc("rate")
        elif key.char == 's':  # Decrease rate
            params["rate"] -= steps["rate"]
            send_osc("rate")
        elif key.char == 'e':  # Increase delay time
            params["delay_time"] += steps["delay_time"]
            send_osc("delay_time")
        elif key.char == 'd':  # Decrease delay time
            params["delay_time"] -= steps["delay_time"]
            send_osc("delay_time")
        elif key.char == 'r':  # Increase delay feedback
            params["delay_feedback"] += steps["delay_feedback"]
            send_osc("delay_feedback")
        elif key.char == 'f':  # Decrease delay feedback
            params["delay_feedback"] -= steps["delay_feedback"]
            send_osc("delay_feedback")
        elif key.char == 't':  # Increase echo phase
            params["echo_phase"] += steps["echo_phase"]
            send_osc("echo_phase")
        elif key.char == 'g':  # Decrease echo phase
            params["echo_phase"] -= steps["echo_phase"]
            send_osc("echo_phase")
        elif key.char == 'y':  # Increase echo decay
            params["echo_decay"] += steps["echo_decay"]
            send_osc("echo_decay")
        elif key.char == 'h':  # Decrease echo decay
            params["echo_decay"] -= steps["echo_decay"]
            send_osc("echo_decay")
    except AttributeError:
        # Handle special keys if needed (e.g., arrow keys)
        pass

def on_release(key):
    if key == keyboard.Key.esc:  # Stop listener on 'Escape'
        return False

# Start the keyboard listener
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    print("Listening for key presses. Press 'Esc' to exit.")
    listener.join()
