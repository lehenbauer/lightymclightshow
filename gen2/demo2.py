

# load with ipython %load for now

import time
import sys

from hardware import *
from dispatcher import *
from strip import Strip

physical_strip = initialize_strip()
strip = Strip(physical_strip)

def run_demo(strip):
    """Run the LED demo sequence."""

    # Create dispatcher
    dispatcher = Dispatcher()

    # Run an image in the background
    #FILE = '../symmetric/nEeMBfm.png'
    #FILE = '../sym2/Symmetry-random-26673990-400-320.jpg'
    FILE = '../images/custom/circles1.png'
    # FILE ='../sym2/symmetry_4b3f847e9b02d_hires.jpg'
    image_bg = ImageBackground(strip, FILE)
    print("image")
    dispatcher.run_background_effect(
        image_bg.start(duration=20.0)
    )
    dispatcher.run()

    # Add a background wipe - green (1 second duration)
    wipe = WipeLowHigh(strip)
    dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, duration=3.0))

    dispatcher.run()

    print("wipes")
    inside_out_wipe = WipeInsideOut(strip)
    dispatcher.run_background_effect(inside_out_wipe.start(r=30, g=20, b=50, duration=3.0))

    dispatcher.run()

    outside_in_wipe = WipeOutsideIn(strip)
    dispatcher.run_background_effect(outside_in_wipe.start(r=0, g=20, b=100, duration=3.0))

    dispatcher.run()

    venetian_blinds = VenetianBlinds(strip)
    dispatcher.run_background_effect(venetian_blinds.start(r=0, g=0, b=0, num_blinds=10, duration=1.5))

    dispatcher.run()

    # Add a fade after the wipe - to purple
    fade = FadeBackground(strip)
    dispatcher.run_background_effect(fade.start(r=20, g=0, b=20, duration=3.0))

    dispatcher.run()

    strip.blackout()

    # Add a foreground pulse - blue to white
    print("pulse")
    pulse = Pulse(strip)
    dispatcher.run_foreground_effect(
        pulse.start(center=125, r=0, g=0, b=100, explode_r=255, explode_g=255, explode_b=255, duration=2.0, max_width=50)
    )
    dispatcher.run()

    dispatcher.run_foreground_effect(
        pulse.start(center=225, r=0, g=100, b=0, explode_r=255, explode_g=255, explode_b=255, duration=2.0, max_width=25)
    )
    dispatcher.run()

    strip.blackout()

    # Add sparkles that run for 5 seconds
    sparkle = Sparkle(strip)
    dispatcher.run_foreground_effect(
        sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
    )

    dispatcher.run()

    strip.blackout()

    # Add a continuous chase effect - red at 50 pixels/second
    chase = Chase(strip)
    dispatcher.run_foreground_effect(
        chase.start(r=50, g=0, b=0, speed=50.0, dot_width=10, duration=10)
    )

    # and a continuous chase effect blue at 25 pixels/sec
    chase2 = Chase(strip)
    dispatcher.run_foreground_effect(
        chase2.start(r=0, g=0, b=50, speed=25.0, dot_width=20, duration=10)
    )

    # and bring sparkle back
    dispatcher.run_foreground_effect(
        sparkle.start(r=255, g=255, b=255, density=0.05, duration=10.0)
    )

    strip.blackout()
    # Run the animation
    dispatcher.run()  # Runs until all effects complete

    strip.blackout()

    # To stop a continuous effect manually:
    #dispatcher.stop_foreground_effect(chase)


if __name__ == "__main__":
    try:
        run_demo(strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        strip.blackout()
