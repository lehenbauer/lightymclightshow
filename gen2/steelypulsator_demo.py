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
    """Run the Pulsator demo sequence on both strips."""

    # Create dispatcher and a timeline to hold our effect instances for each strip
    dispatcher = Dispatcher()
    
    # Create timeline objects for each strip
    timelines = []
    for i, strip in enumerate(strips):
        timeline = Timeline()
        
        # --- Instantiate all effects for this strip ---
        timeline.pulsator = SimplePulsator(strip)
        
        timelines.append(timeline)

    # --- Schedule all actions for both strips ---

    # 0.0s: Start the pulsator effect on both strips
    for timeline in timelines:
        dispatcher.schedule(0.0, lambda tl=timeline: dispatcher.run_background_effect(
            tl.pulsator.start(min_node_width_pct=5, max_node_width_pct=20, n_nodes=3, node_pulses=2, low_h=0.7, high_h=0.55, s=1.0, min_v=0.0, max_v=0.5, duration=6)
        ))

    # 6.5s: Second pulsator configuration on both strips (with reversed direction)
    for timeline in timelines:
        dispatcher.schedule(6.5, lambda tl=timeline: dispatcher.run_background_effect(
            tl.pulsator.start(min_node_width_pct=2.5, max_node_width_pct=2.5, n_nodes=10, node_pulses=5, low_h=0.5, high_h=0.6, s=1.0, min_v=0.5, max_v=0.5, duration=10, speed=-20)
        ))

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Pulsator demo complete.")
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
