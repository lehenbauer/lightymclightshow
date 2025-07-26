

class Wipes:
    def __init__(self, strip):
        self.strip = strip
        self.width = strip.numPixels()

    def low_high(self, color, fps=30):
        """ Fills the strip from the first pixel to the last. """
        for i in range(self.width):
            self.strip[i] = color
            self.strip.show()
            self.strip.sleep(1 / fps)

    def high_low(self, color, fps=30):
        """ Fills the strip from the last pixel to the first. """

        for i in range(self.width - 1, -1, -1):
            self.strip[i] = color
            self.strip.show()
            self.strip.sleep(1 / fps)

    def outside_in(self, color, fps=30):
        """ Fills the strip from both ends towards the center. """

        for i in range(self.width // 2):
            self.strip[i] = color
            self.strip[self.width - 1 - i] = color
            self.strip.show()
            self.strip.sleep(1 / fps)

        # finally, light up the center pixel last if there are an odd number
        if self.width % 2 == 1:
            self.strip[self.width // 2] = color
            self.strip.show()
            self.strip.sleep(1 / fps)

    def inside_out(self, color, fps=30):
        """ Fills the strip from the center outwards to both ends. """

        # light up the center pixel first if there are an odd number
        if self.width % 2 == 1:
            self.strip[self.width // 2] = color
            self.strip.show()
            self.strip.sleep(1 / fps)

        for i in range(self.width // 2):
            self.strip[self.width - 1 - i] = color
            self.strip[i] = color
            self.strip.show()
            self.strip.sleep(1 / fps)


