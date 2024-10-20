
from pathlib import Path

def get_image_files_recursive(directory, recursive = False):
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

# Example Usage
if __name__ == "__main__":
    directory_path = 'sym2'  # Replace with your directory path
    try:
        images = get_image_files_recursive(directory_path)
        print(f"Found {len(images)} image(s) recursively:")
        for img in images:
            print(img)
    except ValueError as ve:
        print(ve)

