

import time
import sys

from steelyglint import *
from dispatcher import *
from strip import Strip

physical_strips = initialize_strips()
strips = [Strip(ps) for ps in physical_strips]

def run_demo(strips):
    """Run the LED demo sequence on both strips."""

    # Create dispatcher and a timeline to hold our effect instances for each strip
    dispatcher = Dispatcher()
    
    # Create timeline objects for each strip
    timelines = []
    for i, strip in enumerate(strips):
        timeline = Timeline()
        
        # --- Instantiate all effects for this strip ---
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
        
        timelines.append(timeline)

    # --- Schedule all actions for both strips ---

    # 0.0s: Start a 20s image background on both strips
    for timeline in timelines:
        dispatcher.schedule(0.0, lambda tl=timeline: dispatcher.run_background_effect(
            tl.image_bg.start(duration=20.0)
        ))

    # 0.0s: A chain of wipes on both strips, each 3s long
    for i, (strip, timeline) in enumerate(zip(strips, timelines)):
        wipe_chain = Chain(strip, [
            lambda tl=timeline: dispatcher.run_background_effect(tl.wipe1.start(r=0, g=20, b=0, duration=3.0)),
            lambda tl=timeline: dispatcher.run_background_effect(tl.wipe2.start(r=30, g=20, b=50, duration=3.0)),
            lambda tl=timeline: dispatcher.run_background_effect(tl.wipe3.start(r=0, g=20, b=100, duration=3.0)),
            lambda tl=timeline: dispatcher.run_background_effect(tl.fade.start(r=20, g=0, b=20, duration=3.0)),
        ])
        wipe_chain.dispatcher = dispatcher
        dispatcher.schedule(0.0, lambda wc=wipe_chain: dispatcher.run_background_effect(wc.start()))


    # 12.5s: Venetian blinds on both strips
    for timeline in timelines:
        dispatcher.schedule(12.5, lambda tl=timeline: dispatcher.run_background_effect(
            tl.venetian_blinds.start(r=0, g=0, b=0, num_blinds=10, duration=1.5)
        ))

    # 14.0s: Blackout both strips before pulses
    for strip in strips:
        dispatcher.schedule(14.0, lambda s=strip: s.blackout())

    # 14.5s: First pulse on both strips
    for timeline in timelines:
        dispatcher.schedule(14.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.pulse.start(center=125, h=0.66, s=1.0, v=1.0, explode_v=1.0, duration=2.0, max_width=50)
        ))

    # 17.0s: Blackout both strips
    for strip in strips:
        dispatcher.schedule(17.0, lambda s=strip: s.blackout())

    # 17.5s: Second pulse on both strips
    for timeline in timelines:
        dispatcher.schedule(17.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.pulse.start(center=225, h=0.33, s=1.0, v=1.0, explode_v=1.0, duration=2.0, max_width=25)
        ))

    # 20.0s: Blackout both strips
    for strip in strips:
        dispatcher.schedule(20.0, lambda s=strip: s.blackout())

    # 20.5s: Sparkles for 5 seconds on both strips
    for timeline in timelines:
        dispatcher.schedule(20.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
        ))

    # 26.0s: Blackout both strips
    for strip in strips:
        dispatcher.schedule(26.0, lambda s=strip: s.blackout())

    # 26.5s: Two chases and sparkles running together for 10s on both strips
    for timeline in timelines:
        dispatcher.schedule(26.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.chase1.start(r=50, g=0, b=0, speed=50.0, dot_width=10, duration=10)
        ))
        dispatcher.schedule(26.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.chase2.start(r=0, g=0, b=50, speed=25.0, dot_width=20, duration=10)
        ))
        dispatcher.schedule(26.5, lambda tl=timeline: dispatcher.run_foreground_effect(
            tl.sparkle.start(r=255, g=255, b=255, density=0.05, duration=10.0)
        ))

    # 37.0s: Final blackout on both strips
    for strip in strips:
        dispatcher.schedule(37.0, lambda s=strip: s.blackout())

    # --- Run the animation ---
    # The dispatcher will now run until all scheduled events and effects are complete.
    dispatcher.run()

    print("Demo complete.")
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
