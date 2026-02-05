from __future__ import annotations

from core import color_classes
from core.version_info import Versions, VersionInfo

ARCHITOOLS_COLOR: color_classes.RGBColor = color_classes.ORANGE
CURVE_COLOR = color_classes.BABY_BLUE
LOCATOR_COLOR = color_classes.LIME
LOCATOR_SIZE = 10.0
TOOL_NAME = "Architools"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release"),
    VersionInfo(name=TOOL_NAME, version="0.0.2", codename="funky chicken", info="generics added"),
    VersionInfo(name=TOOL_NAME, version="0.0.3", codename="funky pigeon", info="tabs added"),
    VersionInfo(name=TOOL_NAME, version="0.0.4", codename="leopard", info="boxy integration"),
    VersionInfo(name=TOOL_NAME, version="0.0.5", codename="banshee", info="boxy-based staircase"),
    VersionInfo(name=TOOL_NAME, version="0.0.6", codename="squirrel", info="window added"),
    VersionInfo(name=TOOL_NAME, version="0.0.7", codename="gopher", info="boxy fixes"),
])
