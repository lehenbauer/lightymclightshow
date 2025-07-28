

# load with ipython %load for now

import time
import sys
import random

from hardware import *
from dispatcher import *
from strip import Strip

physical_strip = initialize_strip()
strip = Strip(physical_strip)

def run_demo(strip):
    """Run the Pulsator demo sequence."""

    # Create dispatcher and a timeline to hold our effect instances
    dispatcher = Dispatcher()
    timeline = Timeline()

    # --- Instantiate all effects and store them on the timeline ---
    timeline.pulsator = SimplePulsator(strip)

    # --- Schedule all actions ---

    # 0.0s: Start the pulsator effect
    dispatcher.schedule(0.0, lambda: dispatcher.run_background_effect(
        timeline.pulsator.start(min_node_width_pct=5, max_node_width_pct=20, n_nodes=3, node_pulses=2, low_h=0.7, high_h=0.55, s=1.0, min_v=0.0, max_v=0.5, duration=6)
    ))

    dispatcher.schedule(6.5, lambda: dispatcher.run_background_effect(
        timeline.pulsator.start(min_node_width_pct=2.5, max_node_width_pct=2.5, n_nodes=10, node_pulses=5, low_h=0.5, high_h=0.6, s=1.0, min_v=0.5, max_v=0.5, duration=10, speed=20)
    ))

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Pulsator demo complete.")
    strip.blackout()


if __name__ == "__main__":
    try:
        run_demo(strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        strip.blackout()
