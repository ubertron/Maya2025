from __future__ import annotations

from enum import Enum
from pathlib import Path

SOURCE_CONTROL_ROOT: Path = Path.home() / "Dropbox/Projects/Unity/AnimationSandbox"
TOOL_NAME = "Path Tool"


class PathType(Enum):
    """Enum for path type."""

    depot_dir = (0, 128, 255)
    depot_file = (0, 216, 255)
    local_dir = (255, 0, 0)
    local_file = (255, 128, 216)
    missing = (128, 128, 128)
    script = (255, 216, 0)
    workspace_dir = (0, 216, 0)
    workspace_file = (128, 255, 128)

    @property
    def color(self) -> str:
        """CSS string representing the color."""
        return f"rgb({', '.join([str(x) for x in self.value])})"


