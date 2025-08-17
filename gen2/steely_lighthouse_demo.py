# load with ipython %load for now

import time
import sys

from dispatcher import *
from steely_logical import *

def run_demo():
    """Run the Lighthouse Sweep demo on the circular strip."""
    
    # Create dispatcher
    dispatcher = Dispatcher()
    
    # Create timeline for the circular strip
    timeline = Timeline()
    
    # --- Instantiate the lighthouse effect ---
    timeline.lighthouse = LighthouseSweep(circular_strip)
    
    # --- Schedule the lighthouse sweep ---
    
    # Start the lighthouse sweep immediately
    # Using the circular strip that goes around the entire boat
    dispatcher.schedule(0.0, lambda: dispatcher.run_foreground_effect(
        timeline.lighthouse.start(
            rotation_speed=0.5,  # One rotation every 2 seconds
            beam_width_pct=5.0,  # 5% of strip width for main beam
            beam_color_h=0.15,   # Warm white/yellow
            beam_intensity=1.0,  # Full brightness
            has_fog=True,        # Add atmospheric fog effect
            duration=30.0        # Run for 30 seconds
        )
    ))
    
    # Optional: Add a second, dimmer sweep going the opposite direction
    # This creates an interesting interference pattern
    timeline.lighthouse2 = LighthouseSweep(circular_strip)
    dispatcher.schedule(2.0, lambda: dispatcher.run_foreground_effect(
        timeline.lighthouse2.start(
            rotation_speed=-0.3,  # Opposite direction, slower
            beam_width_pct=3.0,   # Narrower beam
            beam_color_h=0.0,     # Red tint
            beam_intensity=0.5,   # Dimmer
            has_fog=False,        # No fog for this one
            duration=28.0         # Stop 2 seconds before the first
        )
    ))
    
    # --- Run the animation ---
    print("Lighthouse Sweep demo running on circular strip.")
    print("Watch as the beacon rotates around the boat!")
    print("A second red beam will start after 2 seconds, rotating the opposite way.")
    
    dispatcher.run()
    
    print("Lighthouse Sweep demo complete.")
    circular_strip.blackout()


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        circular_strip.blackout()