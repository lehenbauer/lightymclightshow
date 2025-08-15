
# load with ipython %load for now

import time
import sys
import random

from steelyglint import *
from dispatcher import *
from strip import Strip

physical_strips = initialize_strips()
strips = [Strip(ps) for ps in physical_strips]
dispatcher = Dispatcher()

def run_demo(strips):
    for _ in range(10):
        # Generate pulses for both strips
        for strip in strips:
            for pulse_num in range(random.randint(1, 4)):
                pulse = Pulse(strip)
                dispatcher.run_foreground_effect(
                    pulse.start(
                        center=random.randint(0, strip.width - 1),
                        h=random.random(),
                        s=1.0,
                        v=1.0,
                        explode_h=random.random(),
                        explode_s=random.uniform(0.0, 0.2),  # whitish explosion
                        explode_v=1.0,
                        duration=random.uniform(1.5, 4.0),
                        max_width=random.randint(20, strip.width // 5)
                    )
                )
        dispatcher.run()


if __name__ == "__main__":
    try:
        run_demo(strips)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        for strip in strips:
            strip.blackout()