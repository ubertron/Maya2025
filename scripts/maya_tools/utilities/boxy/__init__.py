from __future__ import annotations

UI_SCRIPT = "from maya_tools.utilities.boxy import boxy_tool; boxy_tool.BoxyTool().restore()"


class BoxyException(Exception):
    """Exception raised for custom error scenarios."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
