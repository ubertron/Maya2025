from __future__ import annotations

import json
import logging

from pathlib import Path

from ams.ams_enums import AssetType
from ams.ams_paths import ASSETS, SOURCE_ART, PROJECT_ROOT
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__, level=logging.INFO)


class Asset:
    """Class to represent an asset."""

    def __init__(self, name: str, asset_type: AssetType, uuid: str, tags: list[str] | None = None):
        self.name = name
        self.asset_type = asset_type
        self.uuid = uuid
        self.tags = tags if tags else []
    
    def __repr__(self):
        return (
            f"Name: [{self.asset_type.name}] {self.name} [{self.uuid}]\n"
            f"Source directory: {self.source_dir} Exists? {self.source_dir.exists()}\n"
            f"Metadata path: {self.metadata_path} Exists? {self.metadata_path.exists()}\n"
            f"Target path: {self.target_path} Exists? {self.target_path.exists()}"
        )

    @property
    def export_dir(self) -> Path:
        return self.source_dir / "Exports"

    @property
    def metadata_path(self) -> Path:
        return self.source_dir / "metadata.json"

    @property
    def source_dir(self) -> Path:
        return SOURCE_ART / self.asset_type.value / self.name
    
    @property
    def tags(self) -> list[str]:
        return self._tags
    
    @tags.setter
    def tags(self, arg: list[str]):
        self._tags = arg

    @property
    def target_path(self) -> Path:
        """Path of the exported asset in the engine"""
        return ASSETS.joinpath(self.asset_type.value, self.name).with_suffix(".fbx")

    def init_metadata(self, force: bool = False):
        if self.metadata_path.exists() and force is False:
            LOGGER.info(f"Metadata found: {self.metadata_path}")
        else:
            self.source_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "asset_type": self.asset_type.name,
                "export_dir": self.export_dir.relative_to(PROJECT_ROOT).as_posix(),
                "name": self.name,
                "project_root": PROJECT_ROOT.as_posix(),
                "source_dir": self.source_dir.relative_to(PROJECT_ROOT).as_posix(),
                "tags": self.tags,
                "target_path": self.target_path.relative_to(PROJECT_ROOT).as_posix(),
                "uuid": self.uuid,
            }
            with self.metadata_path.open("w") as f:
                json.dump(data, f, indent=4)
            LOGGER.info(f"Metadata written to: {self.metadata_path}")


if __name__ == "__main__":
    from core.uuid_utils import generate_uuid
    asset = Asset(name="staveley_court", asset_type=AssetType.environment, uuid=generate_uuid())
    asset.init_metadata(force=True)
