

# load with ipython %load for now

import time
import sys

from hardware import *
from dispatcher import *


def run_demo():
    """Run the LED demo sequence."""
    strip = initialize_strip()

    # Create dispatcher
    dispatcher = Dispatcher(strip)

    # Add a background wipe - green (1 second duration)
    wipe = WipeLowHigh(strip, dispatcher.background)
    dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, duration=3.0))

    dispatcher.run()

    inside_out_wipe = WipeInsideOut(strip, dispatcher.background)
    dispatcher.run_background_effect(inside_out_wipe.start(r=30, g=20, b=50, duration=3.0))

    dispatcher.run()

    outside_in_wipe = WipeOutsideIn(strip, dispatcher.background)
    dispatcher.run_background_effect(outside_in_wipe.start(r=0, g=20, b=100, duration=3.0))

    dispatcher.run()

    venetian_blinds = VenetianBlinds(strip, dispatcher.background)
    dispatcher.run_background_effect(venetian_blinds.start(r=50, g=100, b=50, num_blinds=10, duration=1.5))

    dispatcher.run()

    # Add a fade after the wipe - to purple
    fade = FadeBackground(strip, dispatcher.background)
    dispatcher.run_background_effect(fade.start(r=20, g=0, b=20, duration=3.0))

    dispatcher.run()

    dispatcher.blackout()

    # Add a foreground pulse - blue to white
    pulse = Pulse(strip)
    dispatcher.run_foreground_effect(
        pulse.start(center=50, base_r=0, base_g=0, base_b=100)
    )

    dispatcher.run()

    dispatcher.blackout()

    # Add sparkles that run for 5 seconds
    sparkle = Sparkle(strip)
    dispatcher.run_foreground_effect(
        sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
    )

    dispatcher.run()

    dispatcher.blackout()

    # Add a continuous chase effect - red at 20 pixels/second
    chase = Chase(strip)
    dispatcher.run_foreground_effect(
        chase.start(r=255, g=0, b=0, speed=50.0, dot_width=10, duration=10)
    )

    chase2 = Chase(strip)
    dispatcher.run_foreground_effect(
        chase2.start(r=0, g=0, b=255, speed=25.0, dot_width=20, duration=10)
    )

    dispatcher.blackout()
    # Run the animation
    dispatcher.run()  # Runs until all effects complete

    dispatcher.blackout()

    # To stop a continuous effect manually:
    #dispatcher.stop_foreground_effect(chase)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        try:
            strip = initialize_strip()
            dispatcher = Dispatcher(strip)
            dispatcher.blackout()
        except:
            pass  # If we can't blackout, just exit
        sys.exit(0)
