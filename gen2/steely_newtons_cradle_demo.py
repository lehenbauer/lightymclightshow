# load with ipython %load for now

import time
import sys
import random

from dispatcher import *
from steely_logical import *

strips = [starboard_strip, port_strip]

def run_demo(strips):
    """Run the Newton's Cradle demo sequence on both strips."""
    
    # Create dispatcher
    dispatcher = Dispatcher()
    
    # Create timeline objects for each strip
    timelines = []
    for i, strip in enumerate(strips):
        timeline = Timeline()
        
        # --- Instantiate all effects for this strip ---
        timeline.newtons_cradle = NewtonsCradle(strip)
        
        timelines.append(timeline)
    
    # --- Schedule all actions for both strips ---
    
    # 0.0s: Start the Newton's Cradle effect on both strips
    for timeline in timelines:
        dispatcher.schedule(0.0, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.newtons_cradle.start(
                num_balls=5,
                ball_width_pct=2.0,
                h=0.6,  # Blue-purple color
                s=0.8,
                v=1.0,
                swing_duration=1.0,
                duration=20.0
            )
        ))
    
    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()
    
    print("Newton's Cradle demo complete.")
    for strip in strips:
        strip.blackout()


if __name__ == "__main__":
    try:
        run_demo(strips)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        for strip in strips:
            strip.blackout()