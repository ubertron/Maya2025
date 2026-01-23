"""Class to handle version information for tools.

specify version string as "{num_major}.{num_minor}.{num_increment}"

VERSIONS = Versions(
    versions=[
        VersionInfo(name=TOOL_NAME, version="1.0", codename="cobra", info="Initial release"),
        VersionInfo(name=TOOL_NAME, version="1.0.1", codename="banshee", info="Size field added"),
        VersionInfo(name=TOOL_NAME, version="1.0.2", codename="newt", info="Issue fixed for nodes with children"),
        VersionInfo(name=TOOL_NAME, version="1.0.3", codename="panther", info="Button functions added"),
        VersionInfo(name=TOOL_NAME, version="1.0.4", codename="panther", info="Boxy v2 node implemented"),
    ]
)
"""


from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VersionInfo:
    name: str
    version: str
    codename: str
    info: str

    @property
    def title(self) -> str:
        return f"{self.name} v{self.version} [{self.codename}]"


class Versions:
    def __init__(self, versions: list[VersionInfo]):
        self.versions = versions

    @property
    def title(self) -> str:
        return self.versions[-1].title

    @property
    def minor_versions(self) -> list[VersionInfo]:
        """Return a list of {num_major}.{num_minor} versions only."""
        return [x for x in self.versions if len(x.version.split(".")) == 2]
