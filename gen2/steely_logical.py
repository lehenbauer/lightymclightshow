

# steely glint logic strip definitions

import time
import sys
import random

from gen2.steelyglint import *
from gen2.physical_strip import PhysicalStrip
from gen2.logical_strip import LogicalStrip

physical_strip = initialize_strips()
starboard_physical_strip = physical_strip[0]
port_physical_strip = physical_strip[1]

# create a logic strip for the starboard side.  physically 0 is at the back
# and 469 is at the front, so we want to reverse the order of the pixels
# to put 0 at the front and 469 at the back.
starboard_strip = LogicalStrip()
starboard_strip.add_pixel_range(starboard_physical_strip, len(starboard_physical_strip) -1, 0)

# likewise for the port side, make logical 0 be at the front
port_strip = LogicalStrip()
port_strip.add_pixel_range(port_physical_strip, 0, len(port_physical_strip) -1)

# create a "circular" logical strip that combines the two sides, 0 is at the front of
# the starboard side, and 969 is at the front of the port side.
circular_strip = LogicalStrip()
circular_strip.add_pixel_range(starboard_physical_strip, 0, len(starboard_physical_strip) -1)
circular_strip.add_pixel_range(port_physical_strip, len(port_physical_strip) -1, 0)

