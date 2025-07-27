"""
Strip class that encapsulates a physical LED strip and its
lightymclightshow background buffer and any other meta stuff.
"""

from rpi_ws281x import Color


class Strip:
    """Encapsulates a physical LED strip and its background buffer."""

    def __init__(self, physical_strip):
        """
        Initialize a Strip with a physical LED strip.

        Args:
            physical_strip: An rpi_ws281x PixelStrip object
        """
        self.strip = physical_strip
        self.width = physical_strip.numPixels()
        
        # Background buffer - what pixels return to each frame
        self.background = [Color(0, 0, 0)] * self.width

    def blackout(self):
        """ blackout all the pixels in the background array
        and and physically clear the strip."""
        self.clear_background()
        self.copy_background_to_strip()
        self.show()

    def clear_background(self, r=0, g=0, b=0):
        """Set all background pixels to a specific color."""
        color = Color(r, g, b)
        self.background[:] = [color] * self.width

    def copy_background_to_strip(self):
        """Copy the background buffer to the physical strip."""
        for i in range(self.width):
            self.strip.setPixelColor(i, self.background[i])

    def show(self):
        """Update the physical strip to show the current pixel values."""
        self.strip.show()

    def setPixelColor(self, n, color):
        """Set a pixel color directly on the physical strip."""
        self.strip.setPixelColor(n, color)

    def numPixels(self):
        """Return the number of pixels in the strip."""
        return self.width
