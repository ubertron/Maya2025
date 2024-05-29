"""
ProjectDefinition: class for defining key paths for assets and components of a project
save_project_definition(): saves the ProjectDefinition instance to the project root as a .ams file
load_project_definition(): loads the ProjectDefinition instance from the project root .ams file
"""

import pickle
from dataclasses import dataclass
from pathlib import Path
from core.core_enums import Platform, Engine, FileExtension, AssetType


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
    def relative_asset_folder(name: str, asset_type: AssetType, asset_schema: tuple = ()) -> Path:
        return Path(asset_type.value, *asset_schema, name)

    def get_asset_source_art_folder(self, name: str, asset_type: AssetType, asset_schema: tuple = ()) -> Path:
        """
        Get the source art folder for an asset
        :param name:
        :param asset_type:
        :param asset_schema:
        :return:
        """
        relative_folder = self.relative_asset_folder(name=name, asset_type=asset_type, asset_schema=asset_schema)
        return self.source_art_root.joinpath(relative_folder)

    def get_asset_export_folder(self, name: str, asset_type: AssetType, asset_schema: tuple = ()) -> Path:
        """
        Get the export folder for an asset
        :param name:
        :param asset_type:
        :param asset_schema:
        :return:
        """
        relative_folder = self.relative_asset_folder(name=name, asset_type=asset_type, asset_schema=asset_schema)
        return self.exports_root.joinpath(relative_folder)


def save_project_definition(project_definition: ProjectDefinition, project_root: Path):
    """
    Save a project definition to the project root
    :param project_definition:
    :param project_root:
    """
    pickle.dump(project_definition, open(project_root.joinpath(FileExtension.ams.value), 'wb'))


def load_project_definition(project_root: Path) -> ProjectDefinition or None:
    """
    Loads a project definition from file
    :param project_root:
    :return:
    """
    assert project_root.exists(), 'Cannot find project'
    project_definition_path = project_root.joinpath(FileExtension.ams.value)

    if project_definition_path.exists():
        result = pickle.load(open(project_definition_path.as_posix(), 'rb'))

        return result
    else:
        return None


if __name__ == '__main__':
    animation_manager = Path('/Users/andrewdavis/Dropbox/Projects/Unity/AnimationManager')

    my_project_definition = ProjectDefinition(
        root=animation_manager,
        platform=Platform(engine=Engine.unity, version='2021.3.9f1'),
        materials=Path('Assets/Materials'),
        exports=Path('Assets/Models'),
        scenes=Path('Assets/Scenes'),
        textures=Path('Assets/Textures'),
        source_art=Path('SourceArt'),
    )

    # save_project_definition(project_definition=my_project_definition, project_root=animation_manager)
    loaded_definition: ProjectDefinition = load_project_definition(project_root=animation_manager)
    # print(loaded_definition)
    print(loaded_definition.get_asset_folder('clairee', asset_type=AssetType.character, asset_schema=('Cat', 'Female')))
