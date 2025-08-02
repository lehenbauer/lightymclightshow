# HighStriker demo - launches multiple overlapping high striker pucks

import time
import sys
import random

from hardware import *
from dispatcher import *
from strip import Strip

physical_strip = initialize_strip()
strip = Strip(physical_strip)

def run_demo(strip):
    """Run the HighStriker demo with multiple overlapping strikes."""

    # Create dispatcher and a timeline to hold our effect instances
    dispatcher = Dispatcher()
    timeline = Timeline()

    # --- Parameters for the demo ---
    total_strikes = 10
    min_velocity = 80.0  # % of strip per second
    max_velocity = 150.0  # % of strip per second
    min_launch_interval = 0.3  # seconds between launches
    max_launch_interval = 1.0  # seconds between launches
    
    # Different colors for variety
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
    ]

    # --- Schedule all strikes ---
    current_time = 0.0
    
    for i in range(total_strikes):
        # Random velocity for this strike
        velocity = random.uniform(min_velocity, max_velocity)
        
        # Random color
        r, g, b = random.choice(colors)
        
        # Random puck size between 3% and 8%
        puck_size = random.uniform(3.0, 8.0)
        
        # Create a new HighStriker instance for this strike
        striker = HighStriker(strip)
        
        # Schedule it
        dispatcher.schedule(current_time, lambda s=striker, v=velocity, red=r, green=g, blue=b, size=puck_size: 
            dispatcher.run_foreground_effect(
                s.start(r=red, g=green, b=blue, 
                       puck_size_pct=size,
                       launch_velocity_pct_per_sec=v, 
                       acceleration_pct_per_sec2=-50.0)
            ))
        
        # Wait before next strike
        if i < total_strikes - 1:  # Don't wait after the last one
            wait_time = random.uniform(min_launch_interval, max_launch_interval)
            current_time += wait_time
        
        print(f"Strike {i+1}: velocity={velocity:.1f}%, color=({r},{g},{b}), size={puck_size:.1f}%, time={current_time:.2f}s")

    # --- Run the animation ---
    # The dispatcher will run until all effects complete
    print(f"\nLaunching {total_strikes} high striker pucks...")
    dispatcher.run()

    print("\nHigh striker demo complete.")
    strip.blackout()


if __name__ == "__main__":
    try:
        run_demo(strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        strip.blackout()