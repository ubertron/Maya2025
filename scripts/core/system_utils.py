import subprocess

from pathlib import Path


def open_file_location(file_location: Path):
    subprocess.call(['open', '-R', file_location.as_posix()])
