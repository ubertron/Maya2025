"""File Utils."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from core import environment_utils
from core.core_paths import SHELF_DATA, HOTKEYS_DATA

LOGGER = logging.getLogger(__name__)


def edit_hotkeys_data():
    """Edit the Maya shelves in IDE."""
    open_in_pycharm(path=HOTKEYS_DATA)


def edit_shelves_data():
    """Edit the Maya shelves in IDE."""
    open_in_pycharm(path=SHELF_DATA)


def open_in_vs_code(path: Path):
    """Open a file in PyCharm."""
    if path.exists():
        command = ["/Applications/Visual Studio Code.app/Contents/MacOS/Electron", path.as_posix()]
        subprocess.run(command, capture_output=False, text=True)


def open_in_pycharm(path: Path):
    """Open a file in PyCharm."""
    if path.exists():
        command = ["/Applications/PyCharm.app/Contents/MacOS/pycharm", path.as_posix()]
        subprocess.run(command, capture_output=False, text=True)


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
    # edit_shelves_data()
    open_in_vs_code(path=Path("/Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/maya_requirements.txt"))
