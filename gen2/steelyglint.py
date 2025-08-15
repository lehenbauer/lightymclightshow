
# derived from
# NeoPixel library strandtest example
# by Tony DiCola (tony@tonydicola.com)
#
# Modified for Steely Glint with dual light strips

import time
from rpi_ws281x import PixelStrip, Color, ws

# LED strip configuration:
LED_COUNT = 470       # Number of LED pixels per strip
LED_PINS = [18, 10]   # GPIO pins for the two strips (18 uses PWM, 10 uses SPI)

LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10), ignored for SPI
LED_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53, leave at 0 for SPI
LED_STRIP_TYPE = ws.WS2811_STRIP_RGB

def initialize_strips():
    # Create NeoPixel objects for both strips
    strips = []
    for pin in LED_PINS:
        strip = PixelStrip(LED_COUNT, pin, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, strip_type=LED_STRIP_TYPE)
        # Initialize the library (must be called once before other functions)
        strip.begin()
        strips.append(strip)
    return strips

def initialize_strip():
    # Backwards compatibility function that returns just the first strip
    strips = initialize_strips()
    return strips[0]

