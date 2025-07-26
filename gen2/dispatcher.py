import time
import math
import random
from abc import ABC, abstractmethod

import hardware

class Effect(ABC):
    """Base class for all effects."""
    
    def __init__(self, strip):
        self.strip = strip
        self.width = strip.numPixels()
    
    def start(self, **kwargs):
        """Start the effect with given parameters."""
        self.init(**kwargs)
        return self
    
    @abstractmethod
    def init(self, **kwargs):
        """Initialize effect parameters. Override in subclasses."""
        pass
    
    @abstractmethod
    def step(self):
        """
        Step the effect forward one frame.
        Returns True if still active, False if complete.
        """
        pass


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
    
    def __init__(self, strip, fps=30):
        self.strip = strip
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.width = strip.numPixels()
        
        # Background buffer - what pixels return to each frame
        self.background = [(0, 0, 0)] * self.width
        
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
    
    def clear_background(self, color=(0, 0, 0)):
        """Set all background pixels to a specific color."""
        self.background = [color] * self.width
    
    def run_frame(self):
        """Process one frame of animation."""
        frame_start = time.time()
        
        # Step all background effects and remove completed ones
        completed = []
        for effect in self.background_effects:
            if not effect.step():
                completed.append(effect)
        for effect in completed:
            self.background_effects.remove(effect)
        
        # Copy background to strip
        for i in range(self.width):
            self.strip[i] = self.background[i]
        
        # Step all foreground effects and remove completed ones
        completed = []
        for effect in self.foreground_effects:
            if not effect.step():
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
    
    def start(self, **kwargs):
        self.current_pixel = 0
        return super().start(**kwargs)
    
    def init(self, color, speed=1.0):
        self.color = color
        self.pixels_per_frame = max(1, int(self.width / (30 / speed)))
    
    def step(self):
        # Fill pixels for this frame
        end = min(self.current_pixel + self.pixels_per_frame, self.width)
        for i in range(self.current_pixel, end):
            self.background[i] = self.color
        
        self.current_pixel = end
        
        # Return True if still running, False if complete
        return self.current_pixel < self.width


class WipeHighLow(BackgroundEffect):
    """Fills the background from last pixel to first."""
    
    def start(self, **kwargs):
        self.current_pixel = self.width - 1
        return super().start(**kwargs)
    
    def init(self, color, speed=1.0):
        self.color = color
        self.pixels_per_frame = max(1, int(self.width / (30 / speed)))
    
    def step(self):
        # Fill pixels for this frame
        end = max(self.current_pixel - self.pixels_per_frame, -1)
        for i in range(self.current_pixel, end, -1):
            self.background[i] = self.color
        
        self.current_pixel = end
        
        # Return True if still running, False if complete
        return self.current_pixel >= 0


class WipeOutsideIn(BackgroundEffect):
    """Fills the background from both ends towards center."""
    
    def start(self, **kwargs):
        self.current_offset = 0
        return super().start(**kwargs)
    
    def init(self, color, speed=1.0):
        self.color = color
        self.pixels_per_frame = max(1, int(self.width / (60 / speed)))  # /60 because we fill from both sides
        self.max_offset = self.width // 2
    
    def step(self):
        # Fill pixels for this frame
        end = min(self.current_offset + self.pixels_per_frame, self.max_offset)
        for i in range(self.current_offset, end):
            self.background[i] = self.color
            self.background[self.width - 1 - i] = self.color
        
        self.current_offset = end
        
        # Handle center pixel for odd widths when complete
        if self.current_offset >= self.max_offset:
            if self.width % 2 == 1:
                self.background[self.width // 2] = self.color
            return False
        
        return True


class WipeInsideOut(BackgroundEffect):
    """Fills the background from center towards both ends."""
    
    def start(self, **kwargs):
        self.current_offset = 0
        # Handle center pixel first for odd widths
        if self.width % 2 == 1:
            self.background[self.width // 2] = self.color
            self.current_offset = 1
        return super().start(**kwargs)
    
    def init(self, color, speed=1.0):
        self.color = color
        self.pixels_per_frame = max(1, int(self.width / (60 / speed)))
        self.center = self.width // 2
        self.max_offset = self.center + 1
    
    def step(self):
        # Fill pixels for this frame
        end = min(self.current_offset + self.pixels_per_frame, self.max_offset)
        for i in range(self.current_offset, end):
            if self.center - i >= 0:
                self.background[self.center - i] = self.color
            if self.center + i < self.width:
                self.background[self.center + i] = self.color
        
        self.current_offset = end
        
        # Return True if still running, False if complete
        return self.current_offset < self.max_offset


class FadeBackground(BackgroundEffect):
    """Fade the entire background to a target color over time."""
    
    def start(self, **kwargs):
        self.current_frame = 0
        return super().start(**kwargs)
    
    def init(self, target_color, duration=1.0):
        self.target_color = target_color
        self.total_frames = max(1, int(duration * 30))
        
        # Capture starting colors
        self.start_colors = [self.background[i] for i in range(self.width)]
    
    def step(self):
        self.current_frame += 1
        t = self.current_frame / self.total_frames
        
        # Update all pixels
        for i in range(self.width):
            color = []
            for c in range(3):
                start = self.start_colors[i][c]
                end = self.target_color[c]
                value = int(start + (end - start) * t)
                color.append(value)
            self.background[i] = tuple(color)
        
        # Return True if still running, False if complete
        return self.current_frame < self.total_frames


# Foreground Effects

class Pulse(ForegroundEffect):
    """Pulse effect that expands and contracts with brightness changes."""
    
    def start(self, **kwargs):
        self.current_frame = 0
        return super().start(**kwargs)
    
    def init(self, center=None, base_color=(0, 0, 255), max_color=(255, 255, 255), 
            initial_width=10, max_width=None):
        if center is None:
            center = self.width // 2
        if max_width is None:
            max_width = min(self.width, initial_width * 4)
        
        self.center = center
        self.base_color = base_color
        self.max_color = max_color
        self.initial_width = initial_width
        self.max_width = max_width
        
        # Animation timing (in frames at 30fps)
        self.rapid_expansion_frames = 21  # 0.7s
        self.slow_expansion_frames = 9    # 0.3s
        self.slow_decay_frames = 15       # 0.5s
        self.rapid_decay_frames = 15      # 0.5s
        self.total_frames = (self.rapid_expansion_frames + self.slow_expansion_frames + 
                           self.slow_decay_frames + self.rapid_decay_frames)
    
    def step(self):
        # Determine phase and progress
        if self.current_frame < self.rapid_expansion_frames:
            t = self.current_frame / self.rapid_expansion_frames
            width_factor = 1 - math.exp(-3 * t)
            brightness_factor = t ** 1.5
        elif self.current_frame < self.rapid_expansion_frames + self.slow_expansion_frames:
            t = (self.current_frame - self.rapid_expansion_frames) / self.slow_expansion_frames
            width_factor = 0.95 + 0.05 * t
            brightness_factor = 0.9 + 0.1 * t
        elif self.current_frame < self.rapid_expansion_frames + self.slow_expansion_frames + self.slow_decay_frames:
            t = (self.current_frame - self.rapid_expansion_frames - self.slow_expansion_frames) / self.slow_decay_frames
            width_factor = 1.0
            brightness_factor = 1.0 - 0.3 * t
        else:
            t = (self.current_frame - self.rapid_expansion_frames - self.slow_expansion_frames - 
                 self.slow_decay_frames) / self.rapid_decay_frames
            width_factor = 1.0 - 0.5 * t
            brightness_factor = 0.7 * (1 - t) ** 2
        
        # Calculate current width
        width_range = self.max_width - self.initial_width
        current_width = self.initial_width + width_range * width_factor
        
        # Calculate color
        color = []
        for i in range(3):
            base = self.base_color[i]
            target = self.max_color[i]
            value = base + (target - base) * brightness_factor
            color.append(int(min(255, max(0, value))))
        
        # Draw the pulse
        half_width = current_width / 2
        
        for i in range(self.width):
            distance = abs(i - self.center)
            
            if distance <= half_width:
                if half_width > 0:
                    intensity = math.exp(-(distance / half_width) ** 2)
                else:
                    intensity = 1.0 if distance == 0 else 0.0
                
                pixel_color = tuple(int(c * intensity) for c in color)
                self.strip[i] = pixel_color
        
        self.current_frame += 1
        
        # Return True if still running, False if complete
        return self.current_frame < self.total_frames


class Sparkle(ForegroundEffect):
    """Random sparkles that fade in and out."""
    
    def start(self, **kwargs):
        self.sparkles = {}
        return super().start(**kwargs)
    
    def init(self, density=0.1, color=(255, 255, 255), fade_frames=10, duration=None):
        self.density = density
        self.color = color
        self.fade_frames = fade_frames
        self.duration = duration  # None means run forever
        self.elapsed_frames = 0
    
    def step(self):
        # Add new sparkles based on density
        for i in range(self.width):
            if i not in self.sparkles and random.random() < self.density / 30:  # per frame probability
                self.sparkles[i] = self.fade_frames * 2  # fade in + fade out
        
        # Update existing sparkles
        to_remove = []
        for pos, frames in self.sparkles.items():
            if frames > self.fade_frames:
                # Fading in
                t = (self.fade_frames * 2 - frames) / self.fade_frames
            else:
                # Fading out
                t = frames / self.fade_frames
            
            # Apply brightness
            pixel_color = tuple(int(c * t) for c in self.color)
            self.strip[pos] = pixel_color
            
            # Update frame count
            self.sparkles[pos] = frames - 1
            if frames <= 1:
                to_remove.append(pos)
        
        # Remove completed sparkles
        for pos in to_remove:
            del self.sparkles[pos]
        
        self.elapsed_frames += 1
        
        # Check duration if specified
        if self.duration is not None:
            total_frames = int(self.duration * 30)
            return self.elapsed_frames < total_frames
        
        # Run forever if no duration
        return True


class Chase(ForegroundEffect):
    """A dot or group of dots that chase around the strip."""
    
    def start(self, **kwargs):
        self.position = 0
        return super().start(**kwargs)
    
    def init(self, color=(255, 0, 0), dot_size=3, speed=1.0, reverse=False):
        self.color = color
        self.dot_size = dot_size
        self.speed = speed
        self.reverse = reverse
        self.pixels_per_frame = max(1, int(10 * speed))  # Base speed of 10 pixels/sec
    
    def step(self):
        # Draw the dot(s)
        for i in range(self.dot_size):
            pixel_pos = (self.position + i) % self.width
            self.strip[pixel_pos] = self.color
        
        # Move position
        if self.reverse:
            self.position = (self.position - self.pixels_per_frame) % self.width
        else:
            self.position = (self.position + self.pixels_per_frame) % self.width
        
        # Chase runs forever
        return True


# Example usage
"""
# Create dispatcher
dispatcher = Dispatcher(strip)

# Add a background wipe
wipe = WipeLowHigh(strip, dispatcher.background)
dispatcher.add_background_effect(wipe.start(color=(0, 20, 0), speed=1.0))

# Add a fade after the wipe
fade = FadeBackground(strip, dispatcher.background)
dispatcher.add_background_effect(fade.start(target_color=(20, 0, 20), duration=2.0))

# Add a foreground pulse
pulse = Pulse(strip)
dispatcher.add_foreground_effect(pulse.start(center=50, base_color=(0, 0, 100)))

# Add sparkles that run for 5 seconds
sparkle = Sparkle(strip)
dispatcher.add_foreground_effect(sparkle.start(density=0.05, duration=5.0))

# Add a continuous chase effect
chase = Chase(strip)
dispatcher.add_foreground_effect(chase.start(color=(255, 0, 0), speed=2.0))

# Run the animation
dispatcher.run()  # Runs until all effects complete

# To stop a continuous effect manually:
dispatcher.remove_foreground_effect(chase)
"""
