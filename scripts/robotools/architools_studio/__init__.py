from __future__ import annotations

from core.version_info import Versions, VersionInfo

TOOL_NAME = "Architools Studio"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0", codename="lemming", info="architools studio"),
    VersionInfo(name=TOOL_NAME, version="0.1", codename="toad", info="meshbox support"),
    VersionInfo(name=TOOL_NAME, version="0.2", codename="falcon", info="template data model, streamlined UI, boxy linking"),
    VersionInfo(name=TOOL_NAME, version="0.3", codename="otter", info="live editing, Maya sync, UUID tracking"),
    VersionInfo(name=TOOL_NAME, version="0.4", codename="raven", info="boxy tree hierarchy, context menus"),
    VersionInfo(name=TOOL_NAME, version="0.5", codename="fox", info="boxy editor with live size/pivot controls"),
    VersionInfo(name=TOOL_NAME, version="0.6", codename="lynx", info="linked size mode with cycle detection"),
    VersionInfo(name=TOOL_NAME, version="0.7", codename="wolf", info="lock mode with node selector"),
    VersionInfo(name=TOOL_NAME, version="0.8", codename="bear", info="lock calculates distance to target point"),
    VersionInfo(name=TOOL_NAME, version="0.9", codename="hawk", info="offset node modifier"),
    VersionInfo(name=TOOL_NAME, version="1.0", codename="eagle", info="mirror node for symmetry duplication"),
    VersionInfo(name=TOOL_NAME, version="1.1", codename="phoenix", info="parameter nodes with live sliders"),
])
