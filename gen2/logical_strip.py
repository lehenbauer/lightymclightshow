"""
LogicalStrip class that maps logical pixels to physical LED strips.
Allows creating logical strips that span multiple physical strips with
support for reversed pixel ranges.
"""

from rpi_ws281x import Color
from physical_strip import PhysicalStrip


class LogicalStrip:
    """Maps logical strip pixels to one or more physical strips."

    def __init__(self):
        """Initialize an empty logical strip."""
        # Array to store pixel mappings - each element is (strip, physical_pixel_index)
        self._pixel_map = []
        self.width = 0

        # Background buffer for the logical strip
        self.background = []

        # Cache of unique physical strips for efficient show() calls
        self._physical_strips = set()

    def add_pixel_range(self, strip, start_pixel, end_pixel):
        """
        Add a range of pixels from a physical strip to this logical strip.
        Direction is automatically determined: if start > end, pixels are mapped in reverse.

        Args:
            strip: A Strip object
            start_pixel: Starting pixel index in the physical strip
            end_pixel: Ending pixel index in the physical strip (inclusive)

        Example:
            # Map physical pixels 199 to 100 (reversed) to virtual pixels 0-99
            virtual_strip.add_pixel_range(strip1, 199, 100)

            # Map physical pixels 0 to 99 to virtual pixels 100-199
            virtual_strip.add_pixel_range(strip2, 0, 99)
        """
        # Validate bounds
        min_pixel = min(start_pixel, end_pixel)
        max_pixel = max(start_pixel, end_pixel)

        if min_pixel < 0 or max_pixel >= strip.numPixels():
            raise ValueError(f"Pixel range {start_pixel}-{end_pixel} out of bounds for strip with {strip.numPixels()} pixels")

        # Determine direction and add pixels
        if start_pixel <= end_pixel:
            # Forward direction
            for i in range(start_pixel, end_pixel + 1):
                self._pixel_map.append((strip, i))
        else:
            # Reverse direction
            for i in range(start_pixel, end_pixel - 1, -1):
                self._pixel_map.append((strip, i))

        # Update width and background buffer
        self.width = len(self._pixel_map)
        self.background = [Color(0, 0, 0)] * self.width

        # Update cached physical strips set
        self._physical_strips.add(strip)

    def setPixelColor(self, n, color):
        """
        Set a virtual pixel color, which maps to the appropriate physical strip pixel.

        Args:
            n: Virtual pixel index
            color: Color value to set
        """
        if n < 0 or n >= self.width:
            return  # Ignore out of bounds pixels

        strip, physical_idx = self._pixel_map[n]
        strip.setPixelColor(physical_idx, color)

    def numPixels(self):
        """Return the number of pixels in the virtual strip."""
        return self.width

    def blackout(self):
        """Blackout all pixels in the virtual strip."""
        self.set_background()
        self.copy_background_to_strip()
        self.show()

    def set_background(self, r=0, g=0, b=0):
        """Set all background pixels to a specific color."""
        color = Color(r, g, b)
        self.background[:] = [color] * self.width

    def copy_background_to_strip(self):
        """Copy the background buffer to the physical strips."""
        for i in range(self.width):
            self.setPixelColor(i, self.background[i])

    def copy_color_to_strip(self, r=0, g=0, b=0):
        """Copy a specific color to all pixels."""
        color = Color(r, g, b)
        for i in range(self.width):
            self.setPixelColor(i, color)

    def show(self):
        """
        Update all affected physical strips to show current pixel values.
        Only calls show() once per unique physical strip.
        """
        # Use cached set of physical strips
        for strip in self._physical_strips:
            strip.show()

    def __len__(self):
        """Return the number of pixels in the virtual strip."""
        return self.width

    def __getitem__(self, key):
        """
        Get pixel color(s) from the virtual strip.
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
        Set pixel color(s) in the virtual strip.
        Supports single index and slice notation.

        Examples:
            virtual_strip[0] = Color(255, 0, 0)  # Set single pixel
            virtual_strip[10:20] = Color(0, 255, 0)  # Set range of pixels
            virtual_strip[::2] = Color(0, 0, 255)  # Set every other pixel
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
