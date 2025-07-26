
import time

from image_stuff import *
from hardware import *

strip = initialize_strip()

#image_arrays = load_images('new-image-drivers', 300)
image_arrays = load_images('sym2', 300)

def clear(strip):
    black = Color(0, 0, 0)
    for i in range(strip.numPixels()):
        strip[i] = black
    strip.show()

def play_arrays():
    for (filename, image_array) in image_arrays:
        print(filename)
        play_array(strip, image_array)
        clear(strip)
        time.sleep(1)

def play_continuously():
    while True:
        play_arrays()
