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
        self.set_background()
        self.copy_background_to_strip()
        self.show()

    def set_background(self, r=0, g=0, b=0):
        """Set all background pixels to a specific color."""
        color = Color(r, g, b)
        self.background[:] = [color] * self.width

    def copy_background_to_strip(self):
        """Copy the background buffer to the physical strip."""
        for i in range(self.width):
            self.strip.setPixelColor(i, self.background[i])

    def copy_color_to_strip(self, r=0, g=0, b=0):
        """Copy a specific color to the physical strip."""
        color = Color(r, g, b)
        for i in range(self.width):
            self.strip.setPixelColor(i, color)

    def show(self):
        """Update the physical strip to show the current pixel values."""
        self.strip.show()

    def setPixelColor(self, n, color):
        """Set a pixel color directly on the physical strip."""
        self.strip.setPixelColor(n, color)

    def numPixels(self):
        """Return the number of pixels in the strip."""
        return self.width

    def __len__(self):
        """Return the number of pixels in the strip."""
        return self.width

    def __getitem__(self, key):
        """
        Get pixel color(s) from the strip's background buffer.
        Supports single index and slice notation.
        """
        if isinstance(key, int):
            # Single pixel
            if key < 0:
                key = self.width + key
            if key < 0 or key >= self.width:
                raise IndexError(f"Pixel index {key} out of range")
            return self.background[key]
        elif isinstance(key, slice):
            # Slice of pixels
            return self.background[key]
        else:
            raise TypeError(f"Invalid index type: {type(key)}")

    def __setitem__(self, key, color):
        """
        Set pixel color(s) in the strip.
        Supports single index and slice notation.

        Examples:
            strip[0] = Color(255, 0, 0)  # Set single pixel
            strip[10:20] = Color(0, 255, 0)  # Set range of pixels
            strip[::2] = Color(0, 0, 255)  # Set every other pixel
        """
        if isinstance(key, int):
            # Single pixel
            if key < 0:
                key = self.width + key
            if key < 0 or key >= self.width:
                raise IndexError(f"Pixel index {key} out of range")
            self.setPixelColor(key, color)
            self.background[key] = color
        elif isinstance(key, slice):
            # Slice of pixels
            indices = range(*key.indices(self.width))
            for i in indices:
                self.setPixelColor(i, color)
                self.background[i] = color
        else:
            raise TypeError(f"Invalid index type: {type(key)}")
