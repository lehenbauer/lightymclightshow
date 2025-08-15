""" play all the images found recursively in the images dirctory to the lights"""

import time
import sys

from steelyglint import *
from image_stuff import *
from dispatcher import *
from strip import Strip

physical_strips = initialize_strips()
strips = [Strip(ps) for ps in physical_strips]

def load_image_effects(strips, dir, recursive=False):
    """Load image effects for all strips."""
    effects_per_strip = []
    for strip in strips:
        effect_list = []
        for file in list_image_files(dir, recursive):
            effect = ImageBackground(strip, file)
            effect_list.append(effect)
        effects_per_strip.append(effect_list)
    return effects_per_strip

image_effects_per_strip = load_image_effects(strips, '../images', recursive=True)

def run_demo(strips):
    """Run the LED demo sequence on both strips."""

    # Create dispatcher
    dispatcher = Dispatcher()

    # Assuming all strips have the same number of effects
    num_effects = len(image_effects_per_strip[0]) if image_effects_per_strip else 0
    
    for i in range(num_effects):
        # Start the same image on all strips simultaneously
        image_path = image_effects_per_strip[0][i].image_path if image_effects_per_strip else None
        if image_path:
            print(f"Starting effect: {image_path}")
        
        for strip_effects in image_effects_per_strip:
            effect = strip_effects[i]
            dispatcher.run_background_effect(effect.start(duration=10.0))
        
        dispatcher.run() # Wait for background effects to complete

    for strip in strips:
        strip.blackout()

if __name__ == "__main__":
    try:
        run_demo(strips)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        for strip in strips:
            strip.blackout()