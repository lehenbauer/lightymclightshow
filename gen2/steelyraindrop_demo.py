# load with ipython %load for now

import time
import sys
import random

#from steelyglint import *
from dispatcher import *
#from physical_strip import PhysicalStrip

from steely_logical import *

strips = [starboard_strip, port_strip]

def run_demo(strips):
    """Run the Raindrop demo sequence on both strips."""

    # Create dispatcher and a timeline to hold our effect instances for each strip
    dispatcher = Dispatcher()
    
    # Create timeline objects for each strip
    timelines = []
    for i, strip in enumerate(strips):
        timeline = Timeline()
        
        # --- Instantiate all effects for this strip ---
        timeline.gravity_filler = RaindropFill(strip)
        
        timelines.append(timeline)

    # --- Schedule all actions for both strips ---

    # 0.0s: Start the raindrop effect on both strips
    for timeline in timelines:
        dispatcher.schedule(0.0, lambda tl=timeline: dispatcher.run_background_effect(
            tl.gravity_filler.start(color=Color(0,0,255))
            #tl.gravity_filler.start()
        ))

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Raindrop demo complete.")
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
