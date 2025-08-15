

# load with ipython %load for now

import time
import sys

from hardware import *
from dispatcher import *
from physical_strip import PhysicalStrip

strip = initialize_strip()

def run_demo(strip):
    """Run the LED demo sequence."""

    # Create dispatcher and a timeline to hold our effect instances
    dispatcher = Dispatcher()
    timeline = Timeline()

    # --- Instantiate all effects and store them on the timeline ---
    timeline.image_bg = ImageBackground(strip, '../images/custom/circles1.png')
    timeline.wipe1 = WipeLowHigh(strip)
    timeline.wipe2 = WipeInsideOut(strip)
    timeline.wipe3 = WipeOutsideIn(strip)
    timeline.fade = FadeBackground(strip)
    timeline.venetian_blinds = VenetianBlinds(strip)
    timeline.pulse = Pulse(strip)
    timeline.sparkle = Sparkle(strip)
    timeline.chase1 = Chase(strip)
    timeline.chase2 = Chase(strip)

    # --- Schedule all actions ---

    # 0.0s: Start a 20s image background. It will be progressively overwritten by the wipes.
    dispatcher.schedule(0.0, lambda: dispatcher.run_background_effect(
        timeline.image_bg.start(duration=20.0)
    ))

    # 0.0s: A chain of wipes, each 3s long
    wipe_chain = Chain(strip, [
        lambda: dispatcher.run_background_effect(timeline.wipe1.start(r=0, g=20, b=0, duration=3.0)),
        lambda: dispatcher.run_background_effect(timeline.wipe2.start(r=30, g=20, b=50, duration=3.0)),
        lambda: dispatcher.run_background_effect(timeline.wipe3.start(r=0, g=20, b=100, duration=3.0)),
        lambda: dispatcher.run_background_effect(timeline.fade.start(r=20, g=0, b=20, duration=3.0)),
    ])
    # The Chain effect itself needs to be passed to the dispatcher so it can be tracked.
    # We pass the Chain's start method as the scheduled action.
    wipe_chain.dispatcher = dispatcher
    dispatcher.schedule(0.0, lambda: dispatcher.run_background_effect(wipe_chain.start()))


    # 12.5s: Venetian blinds
    dispatcher.schedule(12.5, lambda: dispatcher.run_background_effect(
        timeline.venetian_blinds.start(r=0, g=0, b=0, num_blinds=10, duration=1.5)
    ))

    # 14.0s: Blackout before pulses
    dispatcher.schedule(14.0, lambda: strip.blackout())

    # 14.5s: First pulse
    dispatcher.schedule(14.5, lambda: dispatcher.run_foreground_effect(
        timeline.pulse.start(center=125, h=0.66, s=1.0, v=1.0, explode_v=1.0, duration=2.0, max_width=50)
    ))

    # 17.0s: Blackout
    dispatcher.schedule(17.0, lambda: strip.blackout())

    # 17.5s: Second pulse
    dispatcher.schedule(17.5, lambda: dispatcher.run_foreground_effect(
        timeline.pulse.start(center=225, h=0.33, s=1.0, v=1.0, explode_v=1.0, duration=2.0, max_width=25)
    ))

    # 20.0s: Blackout
    dispatcher.schedule(20.0, lambda: strip.blackout())

    # 20.5s: Sparkles for 5 seconds
    dispatcher.schedule(20.5, lambda: dispatcher.run_foreground_effect(
        timeline.sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
    ))

    # 26.0s: Blackout
    dispatcher.schedule(26.0, lambda: strip.blackout())

    # 26.5s: Two chases and sparkles running together for 10s
    dispatcher.schedule(26.5, lambda: dispatcher.run_foreground_effect(
        timeline.chase1.start(r=50, g=0, b=0, speed=50.0, dot_width=10, duration=10)
    ))
    dispatcher.schedule(26.5, lambda: dispatcher.run_foreground_effect(
        timeline.chase2.start(r=0, g=0, b=50, speed=25.0, dot_width=20, duration=10)
    ))
    dispatcher.schedule(26.5, lambda: dispatcher.run_foreground_effect(
        timeline.sparkle.start(r=255, g=255, b=255, density=0.05, duration=10.0)
    ))

    # 37.0s: Final blackout
    dispatcher.schedule(37.0, lambda: strip.blackout())

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Demo complete.")
    strip.blackout()


if __name__ == "__main__":
    try:
        run_demo(strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        strip.blackout()
