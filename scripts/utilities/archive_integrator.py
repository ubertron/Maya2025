"""Tool to integrate archives."""
import logging
import shutil
import sys

from pathlib import Path

from core import logging_utils

LOGGER = logging_utils.get_logger(__name__, level=logging.INFO)


def integrate_archive(source_dir: Path, destination_dir: Path) -> None:
    """Integrate archive."""
    assert source_dir.is_dir(), "Not a directory"
    assert destination_dir.is_dir(), "Not a directory"

    for path in [x for x in source_dir.rglob("*") if x.is_file() and x.suffix == ".py"]:
        LOGGER.info(path)
        relative_path = path.relative_to(source_dir)
        target_path = destination_dir / relative_path
        LOGGER.info(f"-> {target_path}")
        shutil.copy(path, target_path)



if __name__ == "__main__":
    archive_path = Path("/Users/andrewdavis/Desktop/boxy_maya2022_integration_v2/scripts")
    code_dir = Path("/Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/scripts")
    integrate_archive(source_dir=archive_path, destination_dir=code_dir)
