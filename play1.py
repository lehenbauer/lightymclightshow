
from rpi_ws281x import Color

import mosim2
import hardware

import time

mosim = mosim2.MotionSimulator()

strip = hardware.goob()

black = Color(0, 0, 0)
blue = Color(0, 0, 255)

def runnit():
    while True:
        position, continue_flag = mosim.step()
        print(position)
        strip[position] = blue
        if not continue_flag:
            break
        strip.show()
        time.sleep(0.005)




