

# load with ipython %load for now

import time

from hardware import *
from dispatcher import *

strip = initialize_strip()

def blackout(strip):
    black = Color(0, 0, 0)
    for i in range(strip.numPixels()):
        strip[i] = black
    strip.show()

# Create dispatcher
dispatcher = Dispatcher(strip)

# Add a background wipe
wipe = WipeLowHigh(strip, dispatcher.background)
dispatcher.run_background_effect(wipe.start(color=(0, 20, 0), speed=1.0))

# Add a fade after the wipe
fade = FadeBackground(strip, dispatcher.background)
dispatcher.run_background_effect(fade.start(target_color=(20, 0, 20), duration=2.0))

# Add a foreground pulse
pulse = Pulse(strip)
dispatcher.run_foreground_effect(pulse.start(center=50, base_color=(0, 0, 100)))

# Add sparkles that run for 5 seconds
sparkle = Sparkle(strip)
dispatcher.run_foreground_effect(sparkle.start(density=0.05, duration=5.0))

# Add a continuous chase effect
chase = Chase(strip)
dispatcher.run_foreground_effect(chase.start(color=(255, 0, 0), speed=2.0))

# Run the animation
#dispatcher.run()  # Runs until all effects complete
dispatcher.run(duration=20)  # Runs for 20s

# To stop a continuous effect manually:
#dispatcher.remove_foreground_effect(chase)


