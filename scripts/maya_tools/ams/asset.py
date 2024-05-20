import os

from pathlib import Path

from core.core_enums import FileExtension, AssetType


class Asset:
    def __init__(self, source_folder: Path, asset_type: AssetType):
        self.source_folder: Path = source_folder
        self.asset_type: AssetType = asset_type

    def __repr__(self):
        info = f'Name: {self.name} [{self.asset_type.name}]\nPath: {self.source_folder}'
        info += f'\nScene File: {self.scene_file} Exists? {self.scene_file_exists}\nAnimations:'

        if len(self.animations):
            info += '\n- ' + '\n- '.join([str(x) for x in self.animations])
        else:
            info += 'None'

        return info

    @property
    def name(self):
        return self.source_folder.name

    @property
    def scene_file(self):
        return f'{self.name}{FileExtension.mb.value}'

    @property
    def scene_file_path(self):
        return self.source_folder.joinpath(self.scene_file)

    @property
    def scene_file_exists(self):
        return self.source_folder.joinpath(self.scene_file).exists()

    @property
    def all_scene_files(self):
        return [x for x in os.listdir(self.source_folder) if x.endswith(FileExtension.mb.value)]

    @property
    def animations(self):
        return [x for x in self.all_scene_files if x.startswith(f'{self.name}_')]

    @property
    def animation_paths(self):
        return [self.source_folder.joinpath(x) for x in self.animations]


if __name__ == '__main__':
    clairee_folder = Path.home().joinpath('Dropbox/Projects/Unity/AnimationManager/SourceArt/Characters/clairee')
    clairee_asset = Asset(source_folder=clairee_folder, asset_type=AssetType.character)
    print(clairee_asset)
