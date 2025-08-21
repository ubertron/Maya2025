"""File Utils."""
from __future__ import annotations

import subprocess
from pathlib import Path
from core import environment_utils

def open_in_finder(path: Path):
    try:
        subprocess.call(["open", "-R", path])
        print(f"Opened '{path}' in Finder.")
    except FileNotFoundError:
        print("Error: 'open' command not found. This function is for macOS only.")
    except Exception as e:
        print(f"An error occurred: {e}")


def sanitize_path_string(path_string: str) -> Path:
    """Remove quotes from path string."""
    if environment_utils.is_using_windows():
        path_string = path_string.replace("/", "\\")
    if path_string.startswith(("'", '"')):
        path_string = path_string[1:]
    if path_string.endswith(("'", '"')):
        path_string = path_string[:-1]
    return path_string
