import time
import math
import random
import heapq
from abc import ABC, abstractmethod
from rpi_ws281x import Color
from image_stuff import load_and_resize_image, get_row_pixels, list_image_files


class Timeline:
    """A simple container to hold references to effects for scheduling."""
    pass


class Effect(ABC):
    """Base class for all effects."""

    def __init__(self, strip):
        self.strip = strip
        self.width = strip.width
        self.pause_until = 0
        self.pause_started_at = 0

    def start(self, **kwargs):
        """Start the effect with given parameters."""
        self.start_time = time.time()
        self.init(**kwargs)
        return self

    def request_pause(self, duration):
        """
        Request a pause for this effect.
        The dispatcher will not step this effect until the pause is over.
        The effect's elapsed time will not advance during the pause.
        """
        now = time.time()
        self.pause_until = now + duration
        self.pause_started_at = now

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

    def __init__(self, strip):
        super().__init__(strip)
        self.background = strip.background


class ForegroundEffect(Effect):
    """Base class for effects that modify foreground pixels."""
    pass


class Chain(Effect):
    """An effect that runs a sequence of other effects."""

    def __init__(self, strip, effects):
        super().__init__(strip)
        self.effects = list(effects)  # Make a copy
        self.current_effect = None

    def init(self):
        # The start method of the chain doesn't need extra params,
        # but the effects within it do.
        pass

    def start(self):
        """Starts the chain."""
        super().start()
        self._run_next_effect()
        return self

    def _run_next_effect(self):
        """Runs the next effect in the chain."""
        if self.effects:
            self.current_effect = self.effects.pop(0)
            # The "effects" in the list are actually pre-configured start calls
            # e.g. lambda: some_effect.start(duration=2.0)
            self.current_effect()
        else:
            self.current_effect = None

    def step(self, elapsed_time):
        """
        The chain's step is a bit different. It just needs to know when the
        entire sequence is done. It relies on the dispatcher to step the
        actual active effect. The chain is "done" when there are no more
        effects to run and the current one is no longer in the dispatcher's
        active list.
        """
        if self.current_effect:
            # Check if the current effect has finished
            if self.current_effect not in self.dispatcher.background_effects and \
               self.current_effect not in self.dispatcher.foreground_effects:
                self._run_next_effect()

        # The chain is active as long as it has a current effect or more to run
        return self.current_effect is not None


class Dispatcher:
    """Manages the animation loop for effects across multiple strips."""

    def __init__(self, fps=100):
        self.fps = fps
        self.frame_time = 1.0 / fps

        # Active effects
        self.background_effects = []
        self.foreground_effects = []

        # Timing
        self.frame_count = 0
        self.start_time = None
        self.event_queue = []
        self.schedule_count = 0

    def schedule(self, fire_time, action):
        """
        Schedule an action to run at a specific time.
        fire_time: virtual time in seconds to run the action.
        action: A callable (e.g., a function or lambda) to execute.
        """
        entry = (fire_time, self.schedule_count, action)
        heapq.heappush(self.event_queue, entry)
        self.schedule_count += 1

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

    def run_frame(self):
        """Process one frame of animation."""
        frame_start = time.time()
        now = time.time()

        # Group effects by strip for efficient processing
        strips_to_update = set()

        # Step all background effects and remove completed ones
        completed = []
        for effect in self.background_effects:
            if effect.pause_started_at > 0 and now >= effect.pause_until:
                # Pause is over, correct the start time
                actual_pause_duration = now - effect.pause_started_at
                effect.start_time += actual_pause_duration
                effect.pause_started_at = 0

            if now < effect.pause_until:
                strips_to_update.add(effect.strip)
                continue

            elapsed = now - effect.start_time
            if not effect.step(elapsed):
                completed.append(effect)
            else:
                strips_to_update.add(effect.strip)
        for effect in completed:
            self.background_effects.remove(effect)

        # Copy background to strip for each affected strip
        for strip in strips_to_update:
            strip.copy_background_to_strip()

        # Step all foreground effects and remove completed ones
        completed = []
        for effect in self.foreground_effects:
            if effect.strip not in strips_to_update:
                # no background effect got copied to the strip,
                # so clear the strip to remove residual pixels
                # from prior foreground effects
                effect.strip.copy_color_to_strip()
                strips_to_update.add(effect.strip)

            if effect.pause_started_at > 0 and now >= effect.pause_until:
                # Pause is over, correct the start time
                actual_pause_duration = now - effect.pause_started_at
                effect.start_time += actual_pause_duration
                effect.pause_started_at = 0

            if now < effect.pause_until:
                continue

            elapsed = now - effect.start_time
            if not effect.step(elapsed):
                completed.append(effect)

        for effect in completed:
            self.foreground_effects.remove(effect)

        # Show the frame for all updated strips
        for strip in strips_to_update:
            strip.show()

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
        self.start_time = time.time()

        while True:
            # Process event queue
            virtual_now = time.time() - self.start_time
            while self.event_queue and self.event_queue[0][0] <= virtual_now:
                _, _, action = heapq.heappop(self.event_queue)
                try:
                    action()
                except Exception as e:
                    print(f"Error executing scheduled action: {action}\n{e}")

            self.run_frame()

            if duration and (time.time() - self.start_time) >= duration:
                break

            # Break if no active effects and no pending events
            if not self.background_effects and not self.foreground_effects and not self.event_queue:
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


class VenetianBlinds(BackgroundEffect):
    """Wipes in a new background color using multiple simultaneous wipes like venetian blinds."""

    def init(self, r=255, g=255, b=255, duration=1.0, num_blinds=5):
        self.color = Color(r, g, b)
        self.duration = duration
        self.num_blinds = num_blinds

        # Calculate the size of each blind section
        self.blind_size = self.width // num_blinds
        self.remainder = self.width % num_blinds  # Handle any leftover pixels

    def step(self, elapsed_time):
        # Calculate how much of each blind should be filled at this time
        progress = min(elapsed_time / self.duration, 1.0)

        for blind_index in range(self.num_blinds):
            # Calculate start position for this blind
            blind_start = blind_index * self.blind_size

            # Determine the size of this particular blind
            # Add 1 extra pixel to the first few blinds if there's a remainder
            current_blind_size = self.blind_size
            if blind_index < self.remainder:
                current_blind_size += 1
                # Adjust start position for blinds after the first few
                if blind_index > 0:
                    blind_start += min(blind_index, self.remainder)
            elif self.remainder > 0:
                blind_start += self.remainder

            # Calculate how many pixels in this blind should be filled
            pixels_to_fill = int(current_blind_size * progress)

            # Fill pixels for this blind
            for i in range(pixels_to_fill):
                pixel_pos = blind_start + i
                if pixel_pos < self.width:  # Safety check
                    self.background[pixel_pos] = self.color

        # Return True if still running, False if complete
        return elapsed_time < self.duration

class Pulsator(BackgroundEffect):
    """ pulse in and out according to a sine wave that we use for V of the HSV color space.

        note: this doesn't work as well as i'd like.  Use SimplePulsator instead or
        figure out what's wrong with it and fix it.  thanks..

        duration is the total time for the effect in seconds
        max_v is a multiplier for the V value of the HSV color space
        pulses is the number of full sine wave cycles to complete in the duration
        pulse_nodes is the number of nodes in the strip sine wave, i.e. how many spikes in the strip
        offset is a constant offset added to the v_mul value to shift V up if desired.  if set to 0.2
        for instance it will make sure that the max_v multiplier based on elapsed time and
        nuimber of pulses will never be less than 0.2, so it won't go to zero.  it is ultimately clamped to
        0 to 1 but if you want more LEDs lit at the bottom of the trough, set this higher.
        threshold is a value that is subtracted from the V value to create a dead zone at the bottom of the trough
        because if the result is < 0 it is clamed to 0.
    """

    def init(self, h=0.5, s=1.0, max_v=0.5, pulses=5, pulse_nodes=3, offset=0.2, threshold=0.2, duration=10.0):
        self.duration = duration
        self.max_v = max_v
        self.pulses = pulses
        self.pulse_nodes = pulse_nodes  # Number of nodes in the strip sine wave
        self.offset = offset
        self.threshold = threshold
        self.h = h
        self.s = s

    def step(self, elapsed_time):
        # Calculate the sine wave HSV V value for each pixel
        # something involving elapsed_time / self.duration
        # we need to ramp v up and down between 0 and max_v based on
        # the ratio of elapsed time to duration and the number of pulses
        # there are two kinds of pulses, the overall ramping of v
        # and the number within the strip
        ratio = elapsed_time / self.duration
        v_mul = abs(math.sin(ratio * self.pulses * math.pi)) + self.offset
        for i in range(self.width):
            t = (i / self.width) * self.pulse_nodes * math.pi
            abs_sin_t = abs(math.sin(t))
            v = min(1.0, max(0.0, self.max_v * v_mul * abs_sin_t))
            if v < self.threshold:
                self.background[i] = 0
            else:
                r, g, b = self.hsv_to_rgb(self.h, self.s, v)
                self.background[i] = Color(r, g, b)

        return elapsed_time < self.duration

class SimplePulsator(BackgroundEffect):
    def init(self, min_node_width_pct=5, max_node_width_pct=10, n_nodes=3, node_pulses=5, low_h=0.7, high_h=0.7, s=1.0, min_v=0.1, max_v=1.0, duration=10, speed=0):
        self.duration = duration
        self.min_node_width_pct = min_node_width_pct / 100.0  # Convert to fractional percentage
        self.max_node_width_pct = max_node_width_pct / 100.0  # ditto
        self.n_nodes = n_nodes
        self.node_pulses = node_pulses
        self.low_h = low_h
        self.high_h = high_h
        self.s = s
        self.min_v = min_v
        self.max_v = max_v
        self.speed = speed

    def step(self, elapsed_time):
        # Overall progress for pulsing effect
        # We use a sine wave that completes `node_pulses` cycles over the duration.
        # The result is mapped to a 0.0-1.0 range (pulse_t).
        pulse_angle = (elapsed_time / self.duration) * self.node_pulses * 2 * math.pi
        pulse_t = (math.sin(pulse_angle) + 1) / 2.0

        # Interpolate h, v, and node_width based on the pulse progress
        h = self.low_h + (self.high_h - self.low_h) * pulse_t
        v = self.min_v + (self.max_v - self.min_v) * pulse_t
        node_width_pct = self.min_node_width_pct + (self.max_node_width_pct - self.min_node_width_pct) * pulse_t
        node_width_pixels = node_width_pct * self.width

        # Calculate the color for the lit pixels
        r, g, b = self.hsv_to_rgb(h, self.s, v)
        color = Color(r, g, b)

        # Calculate the movement shift
        speed_pixels_per_sec = self.speed / 100.0 * self.width
        shift = speed_pixels_per_sec * elapsed_time

        # Determine the spacing and start of the first node
        if self.n_nodes > 0:
            spacing = self.width / self.n_nodes
            start_offset = (spacing - node_width_pixels) / 2
        else:
            spacing = 0
            start_offset = 0

        # Clear the background before drawing the new state
        for i in range(self.width):
            self.background[i] = Color(0, 0, 0)

        # Draw the nodes
        for i in range(self.n_nodes):
            node_start_unwrapped = i * spacing + start_offset + shift
            node_end_unwrapped = node_start_unwrapped + node_width_pixels

            # Handle wrapping for wider nodes
            # We draw segments of the node if it wraps around the strip
            for p_offset in range(int(node_width_pixels) + 1):
                p = int(node_start_unwrapped + p_offset) % self.width
                self.background[p] = color

        return elapsed_time < self.duration


class ImageBackground(BackgroundEffect):
    """Play an image row by row into the background array."""

    def __init__(self, strip, image_path):
        """
        Initialize the ImageBackground effect and load the image.

        Args:
            strip: The Strip object
            image_path (str): Path to the image file to load
        """
        super().__init__(strip)
        self.image_path = image_path

        # Load and resize the image to match strip width at instantiation time
        self.pixel_array = load_and_resize_image(image_path, self.width)
        self.image_height = self.pixel_array.shape[0]

    def init(self, duration=10.0, loop=False):
        """
        Initialize the image background effect parameters.

        Args:
            duration (float): How long to play the entire image (in seconds)
            loop (bool): Whether to loop the image playback
        """
        self.duration = duration
        self.loop = loop

        # Track the last row displayed to avoid redundant updates
        self.last_row = -1

        # Calculate time per row
        self.time_per_row = self.duration / self.image_height if self.image_height > 0 else 0

    def step(self, elapsed_time):
        if self.image_height == 0:
            return False

        # Calculate which row should be displayed
        if self.loop:
            # For looping, use modulo to wrap around
            total_progress = elapsed_time / self.time_per_row
            current_row = int(total_progress) % self.image_height
        else:
            # For non-looping, clamp to image height
            progress = min(elapsed_time / self.duration, 1.0)
            current_row = min(int(progress * self.image_height), self.image_height - 1)

        # Only update if we've moved to a new row
        if current_row != self.last_row:
            # Get the row colors
            row_colors = get_row_pixels(self.pixel_array, current_row)

            # Copy row colors to background, handling width mismatch
            for i in range(min(len(row_colors), self.width)):
                self.background[i] = row_colors[i]

            # If the image is narrower than the strip, fill remaining pixels with black
            if len(row_colors) < self.width:
                black = Color(0, 0, 0)
                for i in range(len(row_colors), self.width):
                    self.background[i] = black

            self.last_row = current_row

        # Continue if looping or if we haven't finished the image
        if self.loop:
            return True
        else:
            return elapsed_time < self.duration


# Foreground Effects

class Pulse(ForegroundEffect):
    """
    A firework-like pulse that expands rapidly and then fades.
    The expansion slows down over time, and the color brightens to an explosion
    color before fading out.
    """

    def init(self, center=None, h=0.0, s=1.0, v=1.0,
             explode_h=0.0, explode_s=0.0, explode_v=1.0,
             duration=1.5, max_width=None):

        if center is None:
            center = self.width // 2
        if max_width is None:
            max_width = self.width

        self.center = center
        r, g, b = self.hsv_to_rgb(h, s, v)
        self.base_color = Color(r, g, b)
        explode_r, explode_g, explode_b = self.hsv_to_rgb(explode_h, explode_s, explode_v)
        self.explode_color = Color(explode_r, explode_g, explode_b)
        self.duration = duration
        self.max_width = max_width

    def ease_out_cubic(self, t):
        """Easing function for a natural deceleration."""
        return 1 - pow(1 - t, 3)

    def ease_out_quart(self, t):
        """Easing function for a natural deceleration."""
        return 1 - pow(1 - t, 4)

    def ease_out_quint(self, t):
        """Easing function for a natural deceleration."""
        return 1 - pow(1 - t, 5)

    def step(self, elapsed_time):
        # Normalize time from 0 to 1
        progress = min(elapsed_time / self.duration, 1.0)

        # Use easing function to control expansion
        eased_progress = self.ease_out_quint(progress)

        # --- Width Calculation ---
        # The pulse expands to its maximum width based on the eased progress.
        current_width = self.max_width * eased_progress

        # --- Color and Brightness Calculation ---
        # The color interpolates from explode_color to base_color  it expands.
        # The brightness peaks mid-way and then fades to black.
        color = Effect.interpolate_color(self.explode_color, self.base_color, eased_progress)

        # Brightness fades out over the second half of the duration
        brightness = 1.0
        if progress > 0.5:
            brightness = 1.0 - (progress - 0.5) * 2

        # --- Drawing the Pulse ---
        half_width = current_width / 2
        r, g, b = Effect.unpack_color(color)

        for i in range(self.width):
            distance = abs(i - self.center)

            if distance <= half_width:
                # Intensity is highest at the center and falls off towards the edges
                # using a Gaussian distribution for a soft look.
                if half_width > 0:
                    intensity = math.exp(-(distance / half_width) ** 2)
                else:
                    intensity = 1.0 if distance == 0 else 0.0

                # Apply final brightness fade
                final_intensity = intensity * brightness

                pixel_color = Color(
                    int(r * final_intensity),
                    int(g * final_intensity),
                    int(b * final_intensity)
                )
                self.strip.setPixelColor(i, pixel_color)

        # Return True if still running, False if complete
        return elapsed_time < self.duration

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

        # Add new sparkles based on density
        # The number of sparkles to add is proportional to the strip width,
        # density, and time elapsed since the last frame.
        num_new_sparkles_float = self.width * self.density * self.frame_time
        num_new_sparkles = int(num_new_sparkles_float)
        # Add a fractional sparkle based on probability
        if random.random() < num_new_sparkles_float - num_new_sparkles:
            num_new_sparkles += 1

        for _ in range(num_new_sparkles):
            pos = random.randint(0, self.width - 1)
            # A new sparkle will reset the fade-in of an existing one at the same position
            self.sparkles[pos] = (elapsed_time, True)

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

    def init(self, r=255, g=0, b=0, dot_width=3, speed=10.0, duration=10.0, reverse=False):
        self.color = Color(r, g, b)
        self.dot_width = dot_width
        self.speed = speed # movement in pixels per second
        self.duration = duration
        self.reverse = reverse

    def step(self, elapsed_time):
        # Calculate position based on elapsed time
        distance = self.speed * elapsed_time
        if self.reverse:
            position = (-distance) % self.width
        else:
            position = distance % self.width

        # Draw the dot(s)
        for i in range(self.dot_width):
            pixel_pos = int((position + i) % self.width)
            self.strip.setPixelColor(pixel_pos, self.color)

        if self.duration is not None:
            # If a duration is set, check if we should stop
            return elapsed_time < self.duration

        # If no duration, run continuously
        return True

class BlockFill(BackgroundEffect):
    """
    Fills the strip by animating blocks into place one by one from right to left.
    Includes a pause before each block animation.
    """

    def init(self, r=0, g=0, b=255, block_width_pct=5.0, outline_pct=1.0, speed_pct_per_sec=100.0, pause=0.2):
        self.color = Color(r, g, b)
        self.block_width_pct = block_width_pct / 100.0
        self.outline_pct = outline_pct / 100.0
        self.pause_duration = pause

        # Speed in pixels per second for the animation
        self.speed_pps = (speed_pct_per_sec / 100.0) * self.width

        # Calculate dimensions in pixels
        self.block_width_pixels = int(self.block_width_pct * self.width)
        self.outline_pixels = int(self.outline_pct * self.width)
        self.total_block_width = self.block_width_pixels + self.outline_pixels

        if self.total_block_width <= 0:
            self.num_blocks = 0
        else:
            self.num_blocks = math.ceil(self.width / self.total_block_width)

        # Animation state
        self.current_block_index = 0
        self.block_animation_start_time = 0
        self._calculate_current_block_duration()

        # Start with a pause
        self.request_pause(self.pause_duration)


    def _calculate_current_block_duration(self):
        """Calculates the animation duration for the current block based on speed."""
        if self.current_block_index >= self.num_blocks:
            self.current_block_duration = 0
            return

        # The block's final destination (left edge), calculated from the right.
        # The animation starts from the far left (pixel 0).
        target_start_pos = self.width - (self.current_block_index + 1) * self.total_block_width
        distance_to_travel = max(0, target_start_pos)

        if self.speed_pps > 0:
            self.current_block_duration = distance_to_travel / self.speed_pps
        else:
            self.current_block_duration = 0  # Appears instantly if no speed

        # This marks the beginning of the animation for the current block,
        # relative to the effect's total elapsed time.
        self.block_animation_start_time = time.time() - self.start_time


    def step(self, elapsed_time):
        if self.current_block_index >= self.num_blocks:
            return False  # Effect is complete

        # --- Animation Progress ---
        elapsed_for_block = elapsed_time - self.block_animation_start_time
        progress = min(elapsed_for_block / self.current_block_duration, 1.0) if self.current_block_duration > 0 else 1.0

        # --- Drawing ---
        # Clear the entire background for this frame
        for i in range(self.width):
            self.background[i] = Color(0, 0, 0)

        # Redraw all settled blocks at their final positions (from the right)
        for i in range(self.current_block_index):
            start_pos = self.width - (i + 1) * self.total_block_width
            for p_offset in range(self.block_width_pixels):
                p = start_pos + p_offset
                if 0 <= p < self.width:
                    self.background[p] = self.color

        # Draw the currently animating block
        target_start_pos = self.width - (self.current_block_index + 1) * self.total_block_width
        current_start_pos = int(max(0, target_start_pos) * progress)
        for p_offset in range(self.block_width_pixels):
            p = current_start_pos + p_offset
            if 0 <= p < self.width:
                self.background[p] = self.color

        # --- State Update ---
        if progress >= 1.0:
            # The block is now settled. Increment index for the next block.
            self.current_block_index += 1

            # Request a pause before the next block (or before finishing)
            self.request_pause(self.pause_duration)

            # If there are more blocks, calculate the next duration
            if self.current_block_index < self.num_blocks:
                self._calculate_current_block_duration()

        return True


# Helper class for the GravityFill effect
class _Raindrop:
    def __init__(self, initial_velocity, target_y):
        self.start_time = time.time()
        self.initial_velocity = initial_velocity
        self.target_y = target_y


class RaindropFill(BackgroundEffect):
    """
    Fills the strip with pixels that fall from the top with simulated gravity.
    """

    def init(self, color=Color(0, 0, 64), min_launch_rate=5.0, max_launch_rate=15.0,
             min_initial_velocity=10.0, max_initial_velocity=30.0, acceleration=50.0):
        self.color = color
        self.min_launch_rate = min_launch_rate
        self.max_launch_rate = max_launch_rate
        self.min_initial_velocity = min_initial_velocity
        self.max_initial_velocity = max_initial_velocity
        self.acceleration = acceleration

        # Animation state
        self.active_raindrops = []
        self.pixels_filled = 0
        self.next_launch_time = 0.0

        # Clear the background initially
        for i in range(self.width):
            self.background[i] = Color(0, 0, 0)

    def step(self, elapsed_time):
        if self.pixels_filled >= self.width and not self.active_raindrops:
            return False  # Effect is complete

        now = time.time()

        # 1. Launch new raindrops if it's time
        if now >= self.next_launch_time and self.pixels_filled < self.width:
            target_y = self.width - self.pixels_filled - 1
            initial_velocity = random.uniform(self.min_initial_velocity, self.max_initial_velocity)
            drop = _Raindrop(initial_velocity, target_y)
            self.active_raindrops.append(drop)

            # Schedule the next launch
            launch_rate = random.uniform(self.min_launch_rate, self.max_launch_rate)
            if launch_rate > 0:
                self.next_launch_time = now + (1.0 / launch_rate)
            else:
                # Avoid division by zero, wait a bit
                self.next_launch_time = now + 0.1

        # 2. Clear the background to black
        for i in range(self.width):
            self.background[i] = Color(0, 0, 0)

        # 3. Redraw all settled pixels
        for i in range(self.pixels_filled):
            self.background[self.width - 1 - i] = self.color

        # 4. Update and draw active raindrops
        still_falling = []
        newly_landed = 0
        for drop in self.active_raindrops:
            time_since_launch = now - drop.start_time
            # Physics: pos = v_initial * t + 0.5 * a * t^2
            pos = (drop.initial_velocity * time_since_launch) + (0.5 * self.acceleration * time_since_launch**2)

            if pos >= drop.target_y:
                newly_landed += 1
            else:
                # Still falling, draw it at its current position
                pixel_pos = int(pos)
                if 0 <= pixel_pos < self.width:
                    self.background[pixel_pos] = self.color
                still_falling.append(drop)

        self.active_raindrops = still_falling
        self.pixels_filled += newly_landed

        return True


# Example usage
"""
# Create physical strip and wrap it
from strip import Strip
physical_strip = initialize_strip()
strip = Strip(physical_strip)

# Create dispatcher
dispatcher = Dispatcher()

# Run a background wipe - green (1 second duration)
wipe = WipeLowHigh(strip)
dispatcher.run_background_effect(wipe.start(r=0, g=20, b=0, duration=1.0))

# Run a fade after the wipe - to purple
fade = FadeBackground(strip)
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

# Run an image in the background
image_bg = ImageBackground(strip, 'path/to/image.jpg')
dispatcher.run_background_effect(
    image_bg.start(duration=5.0, loop=True)
)

# Run the animation
dispatcher.run()  # Runs until all effects complete

# To stop a continuous effect manually:
dispatcher.stop_foreground_effect(chase)
dispatcher.stop_background_effect(image_bg)
"""
