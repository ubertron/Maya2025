from __future__ import annotations

import math

from pathlib import Path
from PIL import Image, ImageDraw

from core import color_classes
from core.color_classes import RGBColor
from core.logging_utils import get_logger

LOGGER = get_logger(__name__)


def create_checker(
        path: Path, size: int = 256, count: int = 8,
        color1: RGBColor = color_classes.WHITE,
        color2: RGBColor = color_classes.GREY) -> Path:
    """Create checker texture."""
    square_size = math.floor(size / count)
    image = Image.new("RGB", (size, size), color1.values)
    draw = ImageDraw.Draw(image)
    for x in range(0, size, square_size):
        for y in range(0, size, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                draw.rectangle([x, y, x + square_size, y + square_size], fill=color2.values)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path.as_posix())
    return path


def fill_background(path: Path, output_path: Path, rgb: tuple[int, int, int]):
    """Fill the background of a transparent image."""
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", image.size, rgb + (255,))
    result = Image.alpha_composite(background, image)
    result.save(output_path)


def fill_foreground(path: Path, output_path: Path, rgb: tuple[int, int, int]) -> None:
    """Fill an image with a specified color, preserving transparency.

    Args:
        path: Path to the image file.
        output_path: Output path.
        rgb: Color to fill with, as an RGBA tuple (e.g., (255, 0, 0, 255) for red).
    """
    img = Image.open(path).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    rgba = (*list(rgb), 255)
    for x in range(width):
        for y in range(height):
            if pixels[x, y][3] > 0:  # Check if pixel is not fully transparent
                pixels[x, y] = rgba
    img.save(output_path)


def get_image_size(path: Path) -> tuple[int, int]:
    """Get the size of an image."""
    return Image.open(path).size


def resize_image(path: Path, output_path: Path, resolution: tuple[int, int], show: bool = False) -> None:
    """Resize an image to fit the given width and height."""
    img = Image.open(path)
    resized_img = img.resize(resolution, Image.LANCZOS)
    resized_img.save(output_path.as_posix())
    if show:
        resized_img.show()


def tint_image(path: Path, output_path: Path, rgb: tuple[int, int, int] | RGBColor, show: bool = False) -> None:
    """Tint an image preserving the transparency."""
    try:
        if isinstance(rgb, RGBColor):
            rgb = rgb.values
        img = Image.open(path).convert("RGBA")
        pixels = img.load()
        width, height = img.size
        for x in range(width):
            for y in range(height):
                if pixels[x, y][3] > 0:  # Check if pixel is not fully transparent
                    pixels[x, y] = (*rgb, pixels[x, y][3])
        img.save(output_path)
        LOGGER.info(f"Image tinted and saved to {output_path}")
    except FileNotFoundError:
        print(f"Error: Image not found at {path}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    from core_paths import image_path

    # my_path = image_path("open.png")
    # resize_image(path=image_path("maya_large.png"), output_path=IMAGE_DIR / "maya.png", width=128, height=128, show=True)
    # tint_image(path=image_path("browse_og.png"), output_path=IMAGE_DIR / "browse.png", rgb=color_classes.LIGHT_GREY)
    tint_image(path=image_path("toggle_layer_shading.png"), output_path=image_path("toggle_layer_shading.png"), rgb=color_classes.LIGHT_GREY)
    # tint_image(path=Path("/Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/images/icons/eye.png"), output_path=ICON_DIR / "format.png", rgb=color_classes.LIGHT_GREY)
    # tint_image(path=image_path("fingerprint.png"), output_path=ICON_DIR / "uuid.png", rgb=color_classes.LIGHT_GREY)
    # create_checker(path=Path("/Users/andrewdavis/Dropbox/Projects/Unity/Archive/SeventhStreet/Assets/Textures/checker.png"))
