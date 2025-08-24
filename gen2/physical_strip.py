"""
PhysicalStrip class that extends PixelStrip with background buffer functionality
for lightymclightshow effects.
"""

from rpi_ws281x import PixelStrip, Color, ws


class PhysicalStrip(PixelStrip):
    """Extends PixelStrip with background buffer and convenience methods."""

    def __init__(self, led_count, led_pin, freq_hz,
                 dma, invert, brightness,
                 channel, strip_type=ws.WS2811_STRIP_GRB):
        """
        Initialize a PhysicalStrip with LED configuration.

        Args:
            led_count: Number of LED pixels
            led_pin: GPIO pin connected to the pixels
            freq_hz: LED signal frequency in hertz
            dma: DMA channel to use for generating signal
            invert: True to invert the signal
            brightness: Set to 0 for darkest and 255 for brightest
            channel: Channel for GPIOs 13, 19, 41, 45 or 53
            strip_type: Strip type configuration (default: WS2811_STRIP_GRB)
        """
        # Initialize parent PixelStrip
        super().__init__(led_count, led_pin, freq_hz, dma, invert,
                        brightness, channel, strip_type=strip_type)

        # Use led_count directly instead of len(self) to avoid issues before begin()
        self.width = led_count

        # Background buffer - what pixels return to each frame
        # Initialize this BEFORE calling begin() to avoid any potential recursion
        self.background = [Color(0, 0, 0)] * self.width

        # Initialize the library (must be called once before other functions)
        self.begin()

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
            ws.ws2811_led_set(self._channel, i, self.background[i])

    def copy_color_to_strip(self, r=0, g=0, b=0):
        """Copy a specific color to the physical strip."""
        color = Color(r, g, b)
        for i in range(self.width):
            ws.ws2811_led_set(self._channel, i, color)

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
            # Directly call the underlying C method to avoid recursion
            ws.ws2811_led_set(self._channel, key, color)
            self.background[key] = color
        elif isinstance(key, slice):
            # Slice of pixels
            indices = range(*key.indices(self.width))
            for i in indices:
                # Directly call the underlying C method to avoid recursion
                ws.ws2811_led_set(self._channel, i, color)
                self.background[i] = color
        else:
            raise TypeError(f"Invalid index type: {type(key)}")
