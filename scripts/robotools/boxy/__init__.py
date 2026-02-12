from __future__ import annotations

from core.version_info import Versions, VersionInfo


class BoxyException(Exception):
    """Exception raised for custom error scenarios."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


TOOL_NAME = "Boxy Tool"
VERSIONS = Versions(
    versions=[
        VersionInfo(name=TOOL_NAME, version="0.0.0", codename="cobra", info="Initial release"),
        VersionInfo(name=TOOL_NAME, version="0.0.1", codename="banshee", info="Size field added"),
        VersionInfo(name=TOOL_NAME, version="0.0.2", codename="newt", info="Issue fixed for nodes with children"),
        VersionInfo(name=TOOL_NAME, version="0.0.3", codename="panther", info="Button functions added"),
        VersionInfo(name=TOOL_NAME, version="0.0.4", codename="dumb animals", info="Boxy v2 node implemented"),
        VersionInfo(name=TOOL_NAME, version="0.0.5", codename="treefingers", info="inherit scale"),
    ]
)
