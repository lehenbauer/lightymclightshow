
import time

from image_stuff import *
from hardware import *

strip = initialize_strip()

image_arrays = load_images('symmetric', 300)

def play_arrays():
    for image_array in image_arrays:
        play_array(strip, image_array)
        time.sleep(1)

def play_continuously():
    while True:
        play_arrays()
