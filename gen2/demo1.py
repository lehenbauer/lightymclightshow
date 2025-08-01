

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

# Add a background wipe - green (1 second duration)
wipe = WipeLowHigh(strip, dispatcher.background)
dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, duration=3.0))

dispatcher.run()

# Add a fade after the wipe - to purple
fade = FadeBackground(strip, dispatcher.background)
dispatcher.run_background_effect(fade.start(r=20, g=0, b=20, duration=3.0))

dispatcher.run()

blackout(strip)

# Add a foreground pulse - blue to white
pulse = Pulse(strip)
dispatcher.run_foreground_effect(
    pulse.start(center=50, r=0, g=0, b=100, explode_r=255, explode_g=255, explode_b=255, duration=2.0)
)

dispatcher.run()

blackout(strip)

# Add sparkles that run for 5 seconds
sparkle = Sparkle(strip)
dispatcher.run_foreground_effect(
    sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
)

dispatcher.run()

# Add a continuous chase effect - red at 20 pixels/second
chase = Chase(strip)
dispatcher.run_foreground_effect(
    chase.start(r=255, g=0, b=0, speed=20.0)
)

# Run the animation
dispatcher.run()  # Runs until all effects complete

# To stop a continuous effect manually:
#dispatcher.stop_foreground_effect(chase)
