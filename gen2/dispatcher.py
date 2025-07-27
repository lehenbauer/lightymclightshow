import time
import math
import random
from abc import ABC, abstractmethod
from rpi_ws281x import Color

class Effect(ABC):
    """Base class for all effects."""

    def __init__(self, strip):
        self.strip = strip
        self.width = strip.numPixels()

    def start(self, **kwargs):
        """Start the effect with given parameters."""
        self.start_time = time.time()
        self.init(**kwargs)
        return self

    @abstractmethod
    def init(self, **kwargs):
        """Initialize effect parameters. Override in subclasses."""
        pass

    @abstractmethod
    def step(self, elapsed_time):
        """
        Step the effect forward.
        elapsed_time: Total time in seconds since this effect started
        Returns True if still active, False if complete.
        """
        pass

    @staticmethod
    def unpack_color(color):
        """Unpack a 32-bit color into (r, g, b) components."""
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return r, g, b

    @staticmethod
    def rgb_to_hsv(r, g, b):
        """Convert RGB (0-255) to HSV (0-1, 0-1, 0-1)"""
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        diff = mx - mn

        # Value
        v = mx

        # Saturation
        s = 0 if mx == 0 else diff/mx

        # Hue
        if diff == 0:
            h = 0
        elif mx == r:
            h = ((g - b)/diff + (6 if g < b else 0)) / 6.0
        elif mx == g:
            h = ((b - r)/diff + 2) / 6.0
        else:
            h = ((r - g)/diff + 4) / 6.0

        return h, s, v

    @staticmethod
    def hsv_to_rgb(h, s, v):
        """Convert HSV (0-1, 0-1, 0-1) to RGB (0-255)"""
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        i = i % 6
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

        return int(r * 255), int(g * 255), int(b * 255)

    @staticmethod
    def interpolate_color(color1, color2, t):
        """Interpolate between two colors using HSV space. t should be 0.0 to 1.0"""
        r1, g1, b1 = Effect.unpack_color(color1)
        r2, g2, b2 = Effect.unpack_color(color2)

        h1, s1, v1 = Effect.rgb_to_hsv(r1, g1, b1)
        h2, s2, v2 = Effect.rgb_to_hsv(r2, g2, b2)

        # Handle hue interpolation (shortest path around circle)
        if abs(h2 - h1) > 0.5:
            if h1 > h2:
                h2 += 1.0
            else:
                h1 += 1.0

        h = (h1 + (h2 - h1) * t) % 1.0
        s = s1 + (s2 - s1) * t
        v = v1 + (v2 - v1) * t

        r, g, b = Effect.hsv_to_rgb(h, s, v)
        return Color(r, g, b)


class BackgroundEffect(Effect):
    """Base class for effects that modify background values."""

    def __init__(self, strip, background):
        super().__init__(strip)
        self.background = background


class ForegroundEffect(Effect):
    """Base class for effects that modify foreground pixels."""
    pass


class Dispatcher:
    """Manages the LED strip animation loop with background and foreground effects."""

    def __init__(self, strip, fps=100):
        self.strip = strip
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.width = strip.numPixels()

        # Background buffer - what pixels return to each frame
        self.background = [Color(0, 0, 0)] * self.width

        # Active effects
        self.background_effects = []
        self.foreground_effects = []

        # Timing
        self.frame_count = 0

    def run_background_effect(self, effect):
        """Add a background effect to the active list."""
        self.background_effects.append(effect)
        return effect

    def run_foreground_effect(self, effect):
        """Add a foreground effect to the active list."""
        self.foreground_effects.append(effect)
        return effect

    def stop_background_effect(self, effect):
        """Remove a background effect from the active list."""
        if effect in self.background_effects:
            self.background_effects.remove(effect)

    def stop_foreground_effect(self, effect):
        """Remove a foreground effect from the active list."""
        if effect in self.foreground_effects:
            self.foreground_effects.remove(effect)

    def clear_background(self, r=0, g=0, b=0):
        """Set all background pixels to a specific color."""
        color = Color(r, g, b)
        self.background = [color] * self.width

    def run_frame(self):
        """Process one frame of animation."""
        frame_start = time.time()

        # Step all background effects and remove completed ones
        completed = []
        for effect in self.background_effects:
            elapsed = time.time() - effect.start_time
            if not effect.step(elapsed):
                completed.append(effect)
        for effect in completed:
            self.background_effects.remove(effect)

        # Copy background to strip
        for i in range(self.width):
            self.strip.setPixelColor(i, self.background[i])

        # Step all foreground effects and remove completed ones
        completed = []
        for effect in self.foreground_effects:
            elapsed = time.time() - effect.start_time
            if not effect.step(elapsed):
                completed.append(effect)
        for effect in completed:
            self.foreground_effects.remove(effect)

        # Show the frame
        self.strip.show()

        # Sleep to maintain frame rate
        elapsed = time.time() - frame_start
        sleep_time = self.frame_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

        self.frame_count += 1

    def run(self, duration=None):
        """
        Run the animation loop.
        duration: Run for this many seconds, or forever if None
        """
        start_time = time.time()

        while True:
            self.run_frame()

            if duration and (time.time() - start_time) >= duration:
                break

            # Break if no active effects
            if not self.background_effects and not self.foreground_effects:
                break


# Background Effects (Wipes)

class WipeLowHigh(BackgroundEffect):
    """Fills the background from first pixel to last."""

    def init(self, r=255, g=255, b=255, duration=1.0):
        self.color = Color(r, g, b)
        self.duration = duration

    def step(self, elapsed_time):
        # Calculate how many pixels should be filled at this time
        progress = min(elapsed_time / self.duration, 1.0)
        pixels_to_fill = int(self.width * progress)

        # Fill up to current position
        for i in range(pixels_to_fill):
            self.background[i] = self.color

        # Return True if still running, False if complete
        return elapsed_time < self.duration


class WipeHighLow(BackgroundEffect):
    """Fills the background from last pixel to first."""

    def init(self, r=255, g=255, b=255, duration=1.0):
        self.color = Color(r, g, b)
        self.duration = duration

    def step(self, elapsed_time):
        # Calculate how many pixels should be filled at this time
        progress = min(elapsed_time / self.duration, 1.0)
        pixels_to_fill = int(self.width * progress)

        # Fill from the end
        for i in range(pixels_to_fill):
            self.background[self.width - 1 - i] = self.color

        # Return True if still running, False if complete
        return elapsed_time < self.duration


class WipeOutsideIn(BackgroundEffect):
    """Fills the background from both ends towards center."""

    def init(self, r=255, g=255, b=255, duration=1.0):
        self.color = Color(r, g, b)
        self.duration = duration
        self.max_offset = self.width // 2

    def step(self, elapsed_time):
        # Calculate how many pixels should be filled from each end
        progress = min(elapsed_time / self.duration, 1.0)
        pixels_from_each_end = int(self.max_offset * progress)

        # Fill from both ends
        for i in range(pixels_from_each_end):
            self.background[i] = self.color
            self.background[self.width - 1 - i] = self.color

        # Handle center pixel for odd widths when complete
        if progress >= 1.0 and self.width % 2 == 1:
            self.background[self.width // 2] = self.color

        # Return True if still running, False if complete
        return elapsed_time < self.duration


class WipeInsideOut(BackgroundEffect):
    """Fills the background from center towards both ends."""

    def init(self, r=255, g=255, b=255, duration=1.0):
        self.color = Color(r, g, b)
        self.duration = duration
        self.center = self.width // 2
        self.max_offset = self.center + 1

    def step(self, elapsed_time):
        # Calculate how far from center to fill
        progress = min(elapsed_time / self.duration, 1.0)
        distance_from_center = int(self.max_offset * progress)

        # Handle center pixel first for odd widths
        if self.width % 2 == 1:
            self.background[self.center] = self.color

        # Fill outward from center
        for i in range(1, distance_from_center):
            if self.center - i >= 0:
                self.background[self.center - i] = self.color
            if self.center + i < self.width:
                self.background[self.center + i] = self.color

        # Return True if still running, False if complete
        return elapsed_time < self.duration


class FadeBackground(BackgroundEffect):
    """Fade the entire background to a target color over time."""

    def init(self, r=255, g=255, b=255, duration=1.0):
        self.target_color = Color(r, g, b)
        self.duration = duration

        # Capture starting colors
        self.start_colors = [self.background[i] for i in range(self.width)]

    def step(self, elapsed_time):
        # Calculate interpolation factor
        t = min(elapsed_time / self.duration, 1.0)

        # Update all pixels
        for i in range(self.width):
            self.background[i] = Effect.interpolate_color(
                self.start_colors[i],
                self.target_color,
                t
            )

        # Return True if still running, False if complete
        return elapsed_time < self.duration


# Foreground Effects

class Pulse(ForegroundEffect):
    """Pulse effect that expands and contracts with brightness changes."""

    def init(self, center=None, base_r=0, base_g=0, base_b=255,
            max_r=255, max_g=255, max_b=255, initial_width=10, max_width=None):
        if center is None:
            center = self.width // 2
        if max_width is None:
            max_width = min(self.width, initial_width * 4)

        self.center = center
        self.base_color = Color(base_r, base_g, base_b)
        self.max_color = Color(max_r, max_g, max_b)
        self.initial_width = initial_width
        self.max_width = max_width

        # Animation timing (in seconds)
        self.rapid_expansion_time = 0.7
        self.slow_expansion_time = 0.3
        self.slow_decay_time = 0.5
        self.rapid_decay_time = 0.5
        self.total_duration = (self.rapid_expansion_time + self.slow_expansion_time +
                             self.slow_decay_time + self.rapid_decay_time)

    def step(self, elapsed_time):
        # Determine phase and progress
        if elapsed_time < self.rapid_expansion_time:
            t = elapsed_time / self.rapid_expansion_time
            width_factor = 1 - math.exp(-3 * t)
            brightness_factor = t ** 1.5
        elif elapsed_time < self.rapid_expansion_time + self.slow_expansion_time:
            t = (elapsed_time - self.rapid_expansion_time) / self.slow_expansion_time
            width_factor = 0.95 + 0.05 * t
            brightness_factor = 0.9 + 0.1 * t
        elif elapsed_time < self.rapid_expansion_time + self.slow_expansion_time + self.slow_decay_time:
            t = (elapsed_time - self.rapid_expansion_time - self.slow_expansion_time) / self.slow_decay_time
            width_factor = 1.0
            brightness_factor = 1.0 - 0.3 * t
        else:
            t = (elapsed_time - self.rapid_expansion_time - self.slow_expansion_time -
                 self.slow_decay_time) / self.rapid_decay_time
            t = min(t, 1.0)  # Clamp to avoid negative values
            width_factor = 1.0 - 0.5 * t
            brightness_factor = 0.7 * (1 - t) ** 2

        # Calculate current width
        width_range = self.max_width - self.initial_width
        current_width = self.initial_width + width_range * width_factor

        # Calculate color using interpolation
        color = Effect.interpolate_color(self.base_color, self.max_color, brightness_factor)

        # Draw the pulse
        half_width = current_width / 2

        for i in range(self.width):
            distance = abs(i - self.center)

            if distance <= half_width:
                if half_width > 0:
                    intensity = math.exp(-(distance / half_width) ** 2)
                else:
                    intensity = 1.0 if distance == 0 else 0.0

                # Apply intensity to color
                r, g, b = Effect.unpack_color(color)
                pixel_color = Color(
                    int(r * intensity),
                    int(g * intensity),
                    int(b * intensity)
                )
                self.strip.setPixelColor(i, pixel_color)

        # Return True if still running, False if complete
        return elapsed_time < self.total_duration


class Sparkle(ForegroundEffect):
    """Random sparkles that fade in and out."""

    def init(self, r=255, g=255, b=255, density=0.1, fade_time=0.33, duration=None):
        self.color = Color(r, g, b)
        self.density = density
        self.fade_time = fade_time  # Time to fade in/out
        self.duration = duration  # None means run forever
        self.sparkles = {}  # Dict of position: (start_time, is_fading_in)

    def step(self, elapsed_time):
        # Calculate frame time for density calculation
        if not hasattr(self, 'last_time'):
            self.last_time = 0
        self.frame_time = elapsed_time - self.last_time
        self.last_time = elapsed_time

        # Add new sparkles based on density (sparkles per second)
        for i in range(self.width):
            if i not in self.sparkles and random.random() < self.density * self.frame_time:
                self.sparkles[i] = (elapsed_time, True)

        # Update existing sparkles
        to_remove = []
        r, g, b = Effect.unpack_color(self.color)

        for pos, (start_time, is_fading_in) in self.sparkles.items():
            sparkle_age = elapsed_time - start_time

            if is_fading_in and sparkle_age >= self.fade_time:
                # Switch to fading out
                self.sparkles[pos] = (elapsed_time, False)
                sparkle_age = 0
                is_fading_in = False

            if is_fading_in:
                # Fading in
                t = sparkle_age / self.fade_time
            else:
                # Fading out
                t = 1.0 - (sparkle_age / self.fade_time)
                if sparkle_age >= self.fade_time:
                    to_remove.append(pos)
                    t = 0

            # Apply brightness
            pixel_color = Color(int(r * t), int(g * t), int(b * t))
            self.strip.setPixelColor(pos, pixel_color)

        # Remove completed sparkles
        for pos in to_remove:
            del self.sparkles[pos]

        # Check duration if specified
        if self.duration is not None:
            return elapsed_time < self.duration

        # Run forever if no duration
        return True


class Chase(ForegroundEffect):
    """A dot or group of dots that chase around the strip."""

    def init(self, r=255, g=0, b=0, dot_size=3, speed=10.0, reverse=False):
        self.color = Color(r, g, b)
        self.dot_size = dot_size
        self.speed = speed  # pixels per second
        self.reverse = reverse

    def step(self, elapsed_time):
        # Calculate position based on elapsed time
        distance = self.speed * elapsed_time
        if self.reverse:
            position = (-distance) % self.width
        else:
            position = distance % self.width

        # Draw the dot(s)
        for i in range(self.dot_size):
            pixel_pos = int((position + i) % self.width)
            self.strip.setPixelColor(pixel_pos, self.color)

        # Chase runs forever
        return True


# Example usage
"""
# Create dispatcher
dispatcher = Dispatcher(strip)

# Run a background wipe - green (1 second duration)
wipe = WipeLowHigh(strip, dispatcher.background)
dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, duration=1.0))

# Run a fade after the wipe - to purple
fade = FadeBackground(strip, dispatcher.background)
dispatcher.run_background_effect(fade.start(r=20, g=0, b=20, duration=2.0))

# Run a foreground pulse - blue to white
pulse = Pulse(strip)
dispatcher.run_foreground_effect(
    pulse.start(center=50, base_r=0, base_g=0, base_b=100)
)

# Run sparkles that run for 5 seconds
sparkle = Sparkle(strip)
dispatcher.run_foreground_effect(
    sparkle.start(r=255, g=255, b=255, density=0.05, duration=5.0)
)

# Run a continuous chase effect - red at 20 pixels/second
chase = Chase(strip)
dispatcher.run_foreground_effect(
    chase.start(r=255, g=0, b=0, speed=20.0)
)

# Run the animation
dispatcher.run()  # Runs until all effects complete

# To stop a continuous effect manually:
dispatcher.stop_foreground_effect(chase)
"""
