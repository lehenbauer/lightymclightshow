
from pathlib import Path
from PIL import Image

def list_image_files(directory, recursive = False):
    """ Returns a list of image file paths in the specified directory
    and its subdirectories that Pillow can ingest. This function
    scans the directory recursively once and filters the files based
    on their extensions.

    Args:
        directory (str or Path): The path to the directory to search for image files.

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
        PIL.Image: The resized image.
    """
    image = Image.open(image_path)
    aspect_ratio = image.width / image.height
    new_height = int(new_width / aspect_ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

