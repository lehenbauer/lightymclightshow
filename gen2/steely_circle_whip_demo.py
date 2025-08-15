# load with ipython %load for now

import time
import sys
import random

#from steelyglint import *
from dispatcher import *
#from physical_strip import PhysicalStrip

from steely_logical import *

def run_demo(strip):
    """Run the Circle Whip demo sequence on the circular strip."""

    # Create dispatcher and a timeline to hold our effect instances
    dispatcher = Dispatcher()
    
    # Create timeline object for the strip
    timeline = Timeline()
    
    # --- Instantiate all effects for this strip ---
    timeline.whip1 = CircleWhip(strip)
    timeline.whip2 = CircleWhip(strip)
    timeline.whip3 = CircleWhip(strip)
    
    # --- Schedule all actions ---
    
    # 0.0s: Start a red whip that goes around twice per second (0.5 seconds per circle)
    dispatcher.schedule(0.0, lambda: dispatcher.run_foreground_effect(
        timeline.whip1.start(r=255, g=0, b=0, width_pct=0.5, speed=2.0, duration=5.0)
    ))
    
    # 5.5s: Start a green whip that's wider and slower
    dispatcher.schedule(5.5, lambda: dispatcher.run_foreground_effect(
        timeline.whip2.start(r=0, g=255, b=0, width_pct=2.0, speed=1.0, duration=5.0)
    ))
    
    # 11.0s: Start a blue whip that's very fast
    dispatcher.schedule(11.0, lambda: dispatcher.run_foreground_effect(
        timeline.whip3.start(r=0, g=100, b=255, width_pct=1.0, speed=4.0, duration=5.0)
    ))
    
    # 16.5s: Multiple whips at different speeds and colors running together
    for i in range(3):
        whip = CircleWhip(strip)
        color_r = random.randint(100, 255)
        color_g = random.randint(100, 255)
        color_b = random.randint(100, 255)
        speed = 1.0 + i * 0.5  # Different speeds: 1.0, 1.5, 2.0
        dispatcher.schedule(16.5, lambda w=whip, r=color_r, g=color_g, b=color_b, s=speed: 
            dispatcher.run_foreground_effect(
                w.start(r=r, g=g, b=b, width_pct=0.3, speed=s, duration=8.0)
            ))
    
    # 25.0s: Final blackout
    dispatcher.schedule(25.0, lambda: strip.blackout())
    
    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()
    
    print("Circle Whip demo complete.")
    strip.blackout()


if __name__ == "__main__":
    try:
        # Use the circular strip that goes around both sides of the boat
        run_demo(circular_strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        circular_strip.blackout()