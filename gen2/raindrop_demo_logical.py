

# load with ipython %load for now

import time
import sys
import random

from hardware import *
from dispatcher import *
from physical_strip import PhysicalStrip
from logical_strip import LogicalStrip

physical_strip = initialize_strip()

logical_strip = LogicalStrip()
logical_strip.add_pixel_range(physical_strip, len(physical_strip) -1, 0)

def run_demo(strip):
    """Run the Pulsator demo sequence."""

    # Create dispatcher and a timeline to hold our effect instances
    dispatcher = Dispatcher()
    timeline = Timeline()

    # --- Instantiate all effects and store them on the timeline ---
    timeline.gravity_filler = RaindropFill(logical_strip)

    # --- Schedule all actions ---

    # 0.0s: Start the pulsator effect
    dispatcher.schedule(0.0, lambda: dispatcher.run_background_effect(
        timeline.gravity_filler.start(color=Color(255,255,255))
        #timeline.gravity_filler.start()
    ))

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Block fill demo complete.")
    strip.blackout()


if __name__ == "__main__":
    try:
        run_demo(logical_strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        logical_strip.blackout()
