import json

from dataclasses import dataclass
from pathlib import Path

from core.core_enums import AssetType, FileExtension, MetadataKey
from maya_tools.ams.project_utils import ProjectDefinition, load_project_definition


@dataclass
class AssetMetadata:
    name: str
    asset_type: AssetType
    asset_schema: list[str]
    export_hash: str
    animation_hash_dict: dict
    project: ProjectDefinition

    def __post_init__(self):
        if self.asset_schema is None:
            self.asset_schema = ()

    def __repr__(self) -> str:
        return json.dumps(self.data_dict, indent=4)

    def export(self):
        with open(self.metadata_path.as_posix(), 'w') as outfile:
            json.dump(self.data_dict, outfile, indent=4)

        return self.metadata_path

    @property
    def file_name(self) -> str:
        return f'{self.name}{FileExtension.json.value}'

    @property
    def metadata_path(self) -> Path:
        return self.source_art_folder.joinpath(self.file_name)

    @property
    def source_art_folder(self) -> Path:
        return self.project.get_asset_source_art_folder(
            name=self.name,
            asset_type=self.asset_type,
            asset_schema=self.asset_schema)

    @property
    def data_dict(self) -> dict:
        return {
            MetadataKey.project.name: self.project.name,
            MetadataKey.name.name: self.name,
            MetadataKey.asset_type.name: self.asset_type.name,
            MetadataKey.asset_schema.name: self.asset_schema,
            MetadataKey.export_hash.name: self.export_hash,
            MetadataKey.animations.name: self.animation_hash_dict
        }


def get_asset_metadata_path(name: str, asset_type: AssetType, asset_schema: list[str],
                            project: ProjectDefinition) -> Path:
    """
    Get the expected path of a metadata file
    :param name:
    :param asset_type:
    :param asset_schema:
    :param project:
    :return:
    """
    source_art_folder = project.get_asset_source_art_folder(name=name, asset_type=asset_type, asset_schema=asset_schema)
    return source_art_folder.joinpath(f'{name}{FileExtension.json.value}')


def load_asset_metadata(metadata_path: Path, project: ProjectDefinition) -> AssetMetadata or None:
    """
    Get the AssetMetadata instance from the metadata path if it exists
    :param metadata_path:
    :param project:
    :return:
    """
    if metadata_path.exists():
        with open(metadata_path.as_posix()) as f:
            metadata = json.load(f)

        return AssetMetadata(
            name=metadata[MetadataKey.name.name],
            asset_type=AssetType.__members__[metadata[MetadataKey.asset_type.name]],
            asset_schema=metadata[MetadataKey.asset_schema.name],
            export_hash=metadata[MetadataKey.export_hash.name],
            animation_hash_dict=metadata[MetadataKey.animations.name],
            project=project
        )


if __name__ == '__main__':
    project_root: Path = Path.home().joinpath('Dropbox/Projects/Unity/AnimationManager')
    project_def: ProjectDefinition = load_project_definition(project_root=project_root)
    # data_dict = {
    #     'clairee_idle': '47583646ad68',
    #     'clairee_run': '8d4236465ce8',
    #     'clairee_walk': '47583646ad68',
    # }
    # asset_metadata: AssetMetadata = AssetMetadata(name='clairee', asset_type=AssetType.character, asset_schema=None,
    #                                               export_hash='47583646ad68', animation_hash_dict=data_dict,
    #                                               project=project_def)
    # result = asset_metadata
    # print(result.metadata_path)
    m_path = Path.home().joinpath('Dropbox/Projects/Unity/AnimationManager/SourceArt/Characters/clairee/clairee.json')
    asset_metadata = load_asset_metadata(metadata_path=m_path, project=project_def)
    print('value', asset_metadata)
    # print(asset_metadata.project.platform.engine)
    # print(asset_metadata.asset_type)
    # print(asset_metadata.export_hash)
    # print(asset_metadata.animation_hash_dict)
