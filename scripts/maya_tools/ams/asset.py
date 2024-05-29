import os

from pathlib import Path

from core.core_enums import FileExtension, AssetType, ResourceType, Platform, Engine
from maya_tools.ams.project_utils import ProjectDefinition, load_project_definition
from maya_tools.ams.resource import Resource
from maya_tools.ams.ams_enums import ItemStatus


class Asset:
    def __init__(self, name: str, asset_type: AssetType, project: ProjectDefinition):
        self.name = name
        self.asset_type: AssetType = asset_type
        self.project: ProjectDefinition = project

    def __repr__(self):
        info = f'Name: {self.name} [{self.asset_type.name}]\nPath: {self.source_art_folder}'
        info += f'\nScene File: {self.scene_file_path.name} Exists? {self.scene_file_path.exists()}\nAnimations:'

        if len(self.animations):
            info += '\n- ' + '\n- '.join([str(x) for x in self.animations])
        else:
            info += 'None'

        return info

    @property
    def status(self) -> ItemStatus:
        if self.scene_resource.status is ItemStatus.export:
            return ItemStatus.export

        if next((x for x in self.animation_resources if x.status is ItemStatus.export), None):
            return ItemStatus.export

        return ItemStatus.exported

    @property
    def source_art_folder(self) -> Path:
        return self.project.source_art_root.joinpath(self.asset_type.value, self.name)

    @property
    def export_folder(self) -> Path:
        return self.project.exports_root.joinpath(self.asset_type.value, self.name)

    @property
    def source_art_files(self):
        return [x for x in os.listdir(self.source_art_folder) if x.endswith(FileExtension.mb.value)]

    @property
    def animations(self):
        return [x for x in self.source_art_files if x.startswith(f'{self.name}_')]

    @property
    def animation_paths(self):
        return [self.source_art_folder.joinpath(x) for x in self.animations]

    @property
    def scene_file_path(self) -> Path:
        return self.source_art_folder.joinpath(f'{self.name}{FileExtension.mb.value}')

    @property
    def scene_file_export_path(self) -> Path:
        return self.export_folder.joinpath(f'{self.name}{FileExtension.fbx.value}')

    @property
    def scene_resource(self) -> Resource:
        resource_type = ResourceType.rig if self.asset_type is AssetType.character else ResourceType.scene
        status = ItemStatus.exported if self.scene_file_export_path.exists() else ItemStatus.export
        return Resource(name=self.name, extension=FileExtension.mb, resource_type=resource_type, status=status)

    @property
    def animation_resources(self) -> list[Resource]:
        resources = []

        for animation in self.animation_paths:
            animation_export_path = self.get_export_path(animation_path=animation)
            status = ItemStatus.exported if animation_export_path.exists() else ItemStatus.export
            resource = Resource(name=animation.stem, extension=FileExtension.mb, resource_type=ResourceType.animation,
                                status=status)
            resources.append(resource)

        return resources

    def get_export_path(self, animation_path: Path) -> Path:
        """
        Deduces the export path of an animation file
        Changes the underscore to ampersand for Unity files
        :param animation_path:
        :return:
        """
        if self.project.platform.engine is Engine.unity:
            animation_export_file_name = animation_path.stem.replace("_", "@")
        else:
            animation_export_file_name = animation_path.stem

        return self.export_folder.joinpath(f'{animation_export_file_name}{FileExtension.fbx.value}')

    @property
    def metadata_path(self) -> Path:
        return self.source_art_folder.joinpath(f'{self.name}{FileExtension.json.value}')


if __name__ == '__main__':
    animation_manager: Path = Path.home().joinpath('Dropbox/Projects/Unity/AnimationManager')
    project_definition: ProjectDefinition = load_project_definition(project_root=animation_manager)
    clairee_folder = Path.home().joinpath('Dropbox/Projects/Unity/AnimationManager/SourceArt/Characters/clairee')
    clairee_asset = Asset(name='clairee', asset_type=AssetType.character, project=project_definition)
    print(clairee_asset.scene_resource)
    print('\n'.join(str(x) for x in clairee_asset.animation_resources))
    print(clairee_asset.metadata_path)
