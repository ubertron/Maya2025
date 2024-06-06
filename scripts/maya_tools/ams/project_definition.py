"""
ProjectDefinition: class for defining key paths for assets and components of a project
"""

from dataclasses import dataclass
from pathlib import Path

from core.core_enums import Platform, AssetType


@dataclass
class ProjectDefinition:
    root: Path
    platform: Platform
    materials: Path
    exports: Path
    scenes: Path
    textures: Path
    source_art: Path

    def __repr__(self) -> str:
        return f'{self.name} [{self.platform}] [{"valid" if self.paths_verified else "missing paths"}]'

    @property
    def name(self) -> str:
        return self.root.name

    @property
    def content_folders(self) -> list[Path]:
        return [self.materials_folder, self.exports_root, self.scenes_path, self.source_art_root, self.textures_path]

    @property
    def materials_folder(self) -> Path:
        return self.root.joinpath(self.materials)

    @property
    def exports_root(self) -> Path:
        return self.root.joinpath(self.exports)

    @property
    def scenes_path(self) -> Path:
        return self.root.joinpath(self.scenes)

    @property
    def source_art_root(self) -> Path:
        return self.root.joinpath(self.source_art)

    @property
    def textures_path(self) -> Path:
        return self.root.joinpath(self.textures)

    @property
    def paths_verified(self) -> bool:
        return False not in [x.exists() for x in self.content_folders]

    @staticmethod
    def relative_asset_folder(name: str, asset_type: AssetType, schema: tuple = ()) -> Path:
        return Path(asset_type.value, *schema, name)

    def get_asset_source_art_folder(self, name: str, asset_type: AssetType, schema: tuple = ()) -> Path:
        """
        Get the source art folder for an asset
        :param name:
        :param asset_type:
        :param schema:
        :return:
        """
        relative_folder = self.relative_asset_folder(name=name, asset_type=asset_type, schema=schema)
        return self.source_art_root.joinpath(relative_folder)

    def get_asset_export_folder(self, name: str, asset_type: AssetType, schema: tuple = ()) -> Path:
        """
        Get the export folder for an asset
        :param name:
        :param asset_type:
        :param schema:
        :return:
        """
        relative_folder = self.relative_asset_folder(name=name, asset_type=asset_type, schema=schema)
        return self.exports_root.joinpath(relative_folder)
