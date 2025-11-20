"""Functions to help with the creation of Maya splash screen."""
from __future__ import annotations

import logging
from pathlib import Path

from core import image_utils
from core.logging_utils import get_logger
from core.core_paths import IMAGE_DIR

LOGGER: logging.Logger = get_logger(name=__name__)



def build_splash_screens(path: Path, output_dir: Path | None = None) -> list[Path]:
    """Create the copies of a splash screen from the high resolution path."""
    output_dir = output_dir if output_dir else path.parent
    output_dir.mkdir(exist_ok=True, parents=True)
    resolution_dict = {
        output_dir / "MayaStartupImage.png": (860, 500),
        output_dir / "MayaStartupImage_100.png": (1290, 750),
        output_dir / "MayaStartupImage_200.png": (1720, 1000),
    }
    size = image_utils.get_image_size(path=path)
    if size != (1720, 1000):
        msg = f"Invalid resolution: {size!s}. Image must be 1720 x 1000"
        LOGGER.warning(msg)
    for output_path, resolution in resolution_dict.items():
        image_utils.resize_image(path=path, resolution=resolution, output_path=output_path)
    msg = f"Splash screens created: {', '.join(x.name for x in resolution_dict.keys())}"
    LOGGER.info(msg)
    return list(resolution_dict.keys())


if __name__ == "__main__":
    splash_screen_path = IMAGE_DIR / "splash_screen/maya_screensaver2.png"
    build_splash_screens(path=splash_screen_path, output_dir=IMAGE_DIR / "splash_screen")
