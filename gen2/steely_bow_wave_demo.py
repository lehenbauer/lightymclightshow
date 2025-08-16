# load with ipython %load for now

import time
import sys

from dispatcher import *
from steely_logical import *

strips = [starboard_strip, port_strip]

def run_demo(strips):
    """Run the Bow Wave demo sequence on both strips."""
    
    # Create dispatcher
    dispatcher = Dispatcher()
    
    # Create timeline objects for each strip
    timelines = []
    for i, strip in enumerate(strips):
        timeline = Timeline()
        
        # --- Instantiate all effects for this strip ---
        # Starboard is on the right, so bow is at the beginning (15%)
        # Port is on the left, so bow is also at the beginning (15%)
        # Both strips show waves traveling from bow (front) to stern (back)
        timeline.bow_wave = BowWave(strip)
        
        timelines.append(timeline)
    
    # --- Schedule all actions for both strips ---
    
    # 0.0s: Start the bow wave effect on both strips
    for timeline in timelines:
        dispatcher.schedule(0.0, lambda tl=timeline: dispatcher.run_background_effect(
            tl.bow_wave.start(
                max_speed_knots=18.0,
                bow_position=0.15,  # Bow at 15% from front
                duration=None  # Run continuously
            )
        ))
    
    # --- Run the animation ---
    # The dispatcher will run continuously, reading GPS speed
    print("Bow Wave demo running. GPS speed will control the effect.")
    print("Press Ctrl+C to stop.")
    
    try:
        dispatcher.run()
    except KeyboardInterrupt:
        print("\nStopping bow wave demo...")
    
    print("Bow Wave demo complete.")
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