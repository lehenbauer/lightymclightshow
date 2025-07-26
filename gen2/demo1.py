

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

# Add a background wipe - green
wipe = WipeLowHigh(strip, dispatcher.background)
dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, speed=1.0))

dispatcher.run()

# Add a fade after the wipe - to purple
fade = FadeBackground(strip, dispatcher.background)
dispatcher.run_background_effect(fade.start(r=20, g=0, b=20, duration=2.0))

dispatcher.run()

blackout(strip)

# Add a foreground pulse - blue to white
pulse = Pulse(strip)
dispatcher.run_foreground_effect(
    pulse.start(center=50, base_r=0, base_g=0, base_b=100)
)

dispatcher.run()

blackout(strip)

# Add sparkles that run for 5 seconds
sparkle = Sparkle(strip)
dispatcher.run_foreground_effect(
    sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
)

dispatcher.run()

# Add a continuous chase effect - red
chase = Chase(strip)
dispatcher.run_foreground_effect(
    chase.start(r=255, g=0, b=0, speed=2.0)
)

# Run the animation
dispatcher.run()  # Runs until all effects complete

# To stop a continuous effect manually:
#dispatcher.stop_foreground_effect(chase)
