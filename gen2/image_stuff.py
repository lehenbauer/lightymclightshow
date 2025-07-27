import numpy as np
from pathlib import Path
from PIL import Image
from rpi_ws281x import Color

def list_image_files(directory, recursive = False):
    """ Returns a list of image file paths in the specified directory
    and its subdirectories that Pillow can ingest. This function
    scans the directory recursively once and filters the files based
    on their extensions.

    Args:
        directory (str or Path): The path to the directory to search for image files.
        recursive (bool): Whether to search subdirectories recursively.

    Returns:
        list: A list of image file paths as strings.
    """
    supported_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.tiff', '.tif', '.webp', '.heif', '.avif'
    }

    path = Path(directory)

    if not path.is_dir():
        raise ValueError(f"The provided path '{directory}' is not a valid directory.")

    if recursive:
        files = path.rglob('*')
    else:
        files = path.glob('*')

    image_files = [
        str(file)
        for file in files
        if file.is_file() and file.suffix.lower() in supported_extensions
    ]

    return image_files


def load_and_resize_image(image_path, new_width):
    """ Loads an image from the specified file path and resizes it to the
    specified width while maintaining the aspect ratio.

    Args:
        image_path (str or Path): The path to the image file.
        new_width (int): The desired width of the resized image.

    Returns:
        numpy array of the resized PIL.Image
    """
    image = Image.open(image_path)
    if image.mode == 'RGBA':
        # Create a new image with a black background
        background = Image.new('RGB', image.size, (0, 0, 0))
        # Paste the RGBA image onto the black background, using the alpha channel as a mask
        background.paste(image, (0, 0), image)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
        
    aspect_ratio = image.width / image.height
    new_height = int(new_width / aspect_ratio)
    resized_image = image.resize((new_width, new_height))
    pixel_array = np.array(resized_image)
    return pixel_array


def load_images(image_path, new_width):
    """ Loads and resizes all images in the specified directory
        and returns a list of numpy arrays
    """
    arrays = []
    for file in list_image_files(image_path):
        image_array = load_and_resize_image(file, new_width)
        arrays.append((file, image_array))
    return arrays


def get_row_pixels(pixel_array, row):
    """
    Get pixel values from a specific row of an image as Color objects.

    Args:
        pixel_array (np.ndarray): The NumPy array representing the image's pixel data.
                                  Expected shape: (height, width, 3) for RGB.
        row (int): The row index from the image (0-based).

    Returns:
        list: A list of Color objects for the row.
    """
    if row >= pixel_array.shape[0]:
        raise ValueError(f"Row {row} is out of bounds for the image height {pixel_array.shape[0]}")

    row_colors = []
    for col in range(pixel_array.shape[1]):
        # Extract the RGB values from the pixel array
        r, g, b = pixel_array[row, col]
        # Create Color object
        row_colors.append(Color(int(r), int(g), int(b)))
    
    return row_colors
