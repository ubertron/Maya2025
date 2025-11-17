from __future__ import annotations

from pathlib import Path


def get_incremented_file_path(path: Path):
    """Get the incremented name for a file name."""
    if path.stem[-1].isnumeric():
        num_string = ""
        for x in reversed(path.stem):
            if x.isnumeric():
                num_string = f"{x}{num_string}"
            else:
                break
        count = len(num_string)
        new_name = f"{path.stem[:-count]}{int(num_string) + 1:0{count}d}"
    else:
        new_name = f"{path.stem}.001"
    return path.with_stem(new_name)
