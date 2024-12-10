# Initialize variables
set :pitch, 60    # MIDI note for pitch
set :rate, 1      # Playback rate
set :mode, 1      # Mode for synth (1 or 0 for on/off)
set :delay_time, 0.5  # Delay time in seconds
set :delay_feedback, 0.5  # Delay feedback amount
set :echo_phase, 0.25  # Echo phase in seconds
set :echo_decay, 2     # Echo decay duration

# Live loop to listen for OSC messages
live_loop :osc_listener do
  use_real_time
  
  # Listen for pitch updates
  pitch_message = sync "/osc/pitch"
  set :pitch, pitch_message[0] if pitch_message
  
  # Listen for rate updates
  rate_message = sync "/osc/rate"
  set :rate, rate_message[0] if rate_message
  
  # Listen for mode updates
  mode_message = sync "/osc/mode"
  set :mode, mode_message[0] if mode_message
  
  # Listen for delay time updates
  delay_time_message = sync "/osc/delay_time"
  set :delay_time, delay_time_message[0] if delay_time_message
  
  # Listen for delay feedback updates
  delay_feedback_message = sync "/osc/delay_feedback"
  set :delay_feedback, delay_feedback_message[0] if delay_feedback_message
  
  # Listen for echo phase updates
  echo_phase_message = sync "/osc/echo_phase"
  set :echo_phase, echo_phase_message[0] if echo_phase_message
  
  # Listen for echo decay updates
  echo_decay_message = sync "/osc/echo_decay"
  set :echo_decay, echo_decay_message[0] if echo_decay_message
end

# Live loop to play sine wave based on OSC messages with effects
live_loop :sine_wave do
  # Fetch current parameters
  pitch = get[:pitch]
  rate = get[:rate]
  mode = get[:mode]
  delay_time = get[:delay_time]
  delay_feedback = get[:delay_feedback]
  echo_phase = get[:echo_phase]
  echo_decay = get[:echo_decay]
  
  # Play sine wave if mode is on (mode == 1)
  if mode == 1
    with_fx :echo, phase: echo_phase, decay: echo_decay do
      # with_fx :delay, time: delay_time, feedback: delay_feedback do
      synth :sine, note: pitch, rate: rate, sustain: 0.5, release: 0.5
      # end
    end
  end
  
  # Sleep for the duration of the sustain + release
  sleep 1
end


