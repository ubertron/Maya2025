"""Asset Management System"""
from __future__ import annotations
import logging
from pathlib import Path

from ams import ams_paths
from ams.ams_enums import AssetType
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__, level=logging.INFO)


class AMSProject:
    """Class to handle the project."""
    exclusions = [".mayaSwatches"]

    def __init__(self):
        self.root = ams_paths.PROJECT_ROOT.resolve()

    def __repr__(self) -> str:
        return (
            f"Project name: {self.name}\n"
            f"Project root: {self.root} Exists? {self.root.exists()}\n"
            f"Game directory: {self.game_dir} Exists? {self.game_dir.exists()}\n"
            f"Source art directory: {self.source_art_dir} Exists? {self.source_art_dir.exists()}"
        )

    @property
    def environments(self) -> list[Path]:
        return [x for x in self.source_art_dir.joinpath(AssetType.Environments.name).iterdir() if x.is_dir() and x.name not in self.exclusions]

    @property
    def game_dir(self) -> Path:
        return ams_paths.GAME

    @property
    def name(self) -> str:
        return self.root.name

    @property
    def source_art_dir(self) -> Path:
        return ams_paths.SOURCE_ART

    @property
    def textures_dir(self) -> Path:
        return self.source_art_dir / "Textures"

    @staticmethod
    def create_directories():
        """Create the project directories."""
        for path in (
                ams_paths.CORE,
                ams_paths.THIRD_PARTY,
                ams_paths.TOOLS,
        ):
            path.mkdir(parents=True, exist_ok=True)

        for asset_type in AssetType.names():
            ams_paths.ASSETS.joinpath(asset_type).mkdir(parents=True, exist_ok=True)
            if AssetType[asset_type] not in AssetType.engine_exclusive():
                ams_paths.SOURCE_ART.joinpath(asset_type).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ams_project = AMSProject()
    # ams_project.create_directories()
    print(ams_project)
    print("\n".join(x.as_posix() for x in ams_project.environments))
