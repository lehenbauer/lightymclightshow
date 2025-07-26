

# load with ipython %load for now

import time

from hardware import *

strip = initialize_strip()

def blackout(strip):
    black = Color(0, 0, 0)
    for i in range(strip.numPixels()):
        strip[i] = black
    strip.show()

