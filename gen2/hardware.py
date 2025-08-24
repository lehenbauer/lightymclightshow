
# derived from
# NeoPixel library strandtest example
# by Tony DiCola (tony@tonydicola.com)
#

import time
from rpi_ws281x import Color, ws
from physical_strip import PhysicalStrip

# LED strip configuration:
LED_COUNT = 300       # Number of LED pixels.

#LED_PIN = 18        # GPIO pin connected to the pixels (18 uses PWM!).
LED_PIN = 10          # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).

LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10), ignored for SPI
#LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53, leave at 0 for SPI

LED_STRIP_TYPE = ws.WS2811_STRIP_GRB
# can also be WS2811_STRIP_[RGB,RBG,GRB,GBR,BRG,BGR]

def initialize_strip():
    # Create NeoPixel object with appropriate configuration.
    strip = PhysicalStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, strip_type=LED_STRIP_TYPE)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    return strip

