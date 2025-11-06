"""File Utils."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from core import environment_utils
from core.core_paths import SHELVES_DATA
from core import logging_utils


LOGGER = logging.getLogger(__name__)


def edit_shelves_data():
    """Edit the Maya shelves in IDE."""
    open_in_text_edit(path=SHELVES_DATA)


def open_in_pycharm(path: Path):
    """Open a file in PyCharm."""
    command = ["pycharm", path.as_posix()]
    try:
        # Run the command
        subprocess.run(command, check=True)
        logging.info(f"Successfully opened '{path.as_posix()}' in PyCharm.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error opening file in PyCharm: {e}")
    except FileNotFoundError:
        logging.info("PyCharm command-line launcher not found. Please ensure it is configured correctly.")


def open_in_text_edit(path: Path):
    """Open a file in TextEdit."""
    subprocess.call(['open', '-a', 'TextEdit', path.as_posix()])


def open_in_finder(path: Path):
    try:
        subprocess.call(["open", "-R", path])
        logging.info(f"Opened '{path}' in Finder.")
    except FileNotFoundError:
        logging.info("Error: 'open' command not found. This function is for macOS only.")
    except Exception as e:
        logging.info(f"An error occurred: {e}")


def sanitize_path_string(path_string: str) -> Path:
    """Remove quotes from path string."""
    if environment_utils.is_using_windows():
        path_string = path_string.replace("/", "\\")
    if path_string.startswith(("'", '"')):
        path_string = path_string[1:]
    if path_string.endswith(("'", '"')):
        path_string = path_string[:-1]
    return path_string


if __name__ == "__main__":
    edit_shelves_data()
