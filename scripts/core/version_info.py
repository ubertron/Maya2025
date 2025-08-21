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
