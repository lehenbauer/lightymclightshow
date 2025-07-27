
import time
import sys

from hardware import *
from image_stuff import *
from dispatcher import *
from strip import Strip

physical_strip = initialize_strip()
strip = Strip(physical_strip)

def load_image_effects(strip, dir, recursive=False):
    effect_list = []
    for file in list_image_files(dir, recursive):
        effect = ImageBackground(strip, file)
        effect_list.append(effect)
    return effect_list

image_effects = load_image_effects(strip, '../images', recursive=True)

def run_demo(strip):
    """Run the LED demo sequence."""

    # Create dispatcher
    dispatcher = Dispatcher()

    for effect in image_effects:
        # Run each image effect in the background
        print(f"Starting effect: {effect.image_path}")
        dispatcher.run_background_effect(effect.start(duration=10.0))
        dispatcher.run() # Wait for background effects to complete

    strip.blackout()

if __name__ == "__main__":
    try:
        run_demo(strip)
    except KeyboardInterrupt:
        # Clean up and exit gracefully
        print("\nKeyboard interrupt received. Turning off LEDs and exiting...")
        strip.blackout()
