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
