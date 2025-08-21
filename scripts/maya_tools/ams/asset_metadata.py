import json

from dataclasses import dataclass
from pathlib import Path

from core.core_enums import AssetType, MetadataKey
from maya_tools.ams.asset import Asset
from maya_tools.ams.project_utils import load_project_definition, get_project_definition
from maya_tools.ams.project_definition import ProjectDefinition


@dataclass
class AssetMetadata:
    asset: Asset
    rig_hash: str
    animation_hash_dict: dict

    def __repr__(self) -> str:
        return json.dumps(self.data_dict, indent=4)

    def save(self):
        """
        Save the metadata to a JSON file
        :return:
        """
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.metadata_path.as_posix(), 'w') as outfile:
            json.dump(self.data_dict, outfile, indent=4)

        return self.metadata_path

    @property
    def metadata_path(self) -> Path:
        return self.asset.metadata_path

    @property
    def data_dict(self) -> dict:
        return {
            MetadataKey.project.name: str(self.asset.project),
            MetadataKey.name.name: self.asset.name,
            MetadataKey.asset_type.name: self.asset.asset_type.name,
            MetadataKey.schema.name: self.asset.schema if self.asset.schema else None,
            MetadataKey.source_art_folder.name: self.asset.source_art_folder_relative.as_posix(),
            MetadataKey.export_folder.name: self.asset.export_folder_relative.as_posix(),
            MetadataKey.rig_hash.name: self.rig_hash,
            MetadataKey.animations.name: self.animation_hash_dict
        }


def load_asset_metadata(metadata_path: Path) -> AssetMetadata or None:
    """
    Get the AssetMetadata instance from the metadata path if it exists
    :param metadata_path:
    :return:
    """
    if metadata_path.exists():
        with open(metadata_path.as_posix()) as f:
            asset_metadata = json.load(f)

        project = get_project_definition(file_path=metadata_path)
        name = asset_metadata[MetadataKey.name.name]
        asset_type = AssetType.__members__[asset_metadata[MetadataKey.asset_type.name]]
        schema = asset_metadata[MetadataKey.schema.name]
        asset = Asset(name=name, asset_type=asset_type, project=project, schema=schema)
        rig_hash = asset_metadata[MetadataKey.rig_hash.name]
        animation_hash_dict = asset_metadata[MetadataKey.animations.name]

        return AssetMetadata(asset=asset, rig_hash=rig_hash, animation_hash_dict=animation_hash_dict)


if __name__ == '__main__':
    project_root: Path = Path.home().joinpath('Dropbox/Projects/Unity/AnimationSandbox')
    animation_sandbox: ProjectDefinition = load_project_definition(project_root=project_root)
    data_dict = {
        'clairee_idle': '47583646ad68',
        'clairee_run': '8d4236465ce8',
        'clairee_walk': '47583646ad68',
    }
    clairee_asset: Asset = Asset(name='clairee', asset_type=AssetType.character, project=animation_sandbox)
    # clairee_asset: Asset = Asset(name='clairee', asset_type=AssetType.character, project=animation_sandbox, schema=['Scout', 'Girl'])
    metadata: AssetMetadata = AssetMetadata(asset=clairee_asset, rig_hash='47583646ad68', animation_hash_dict=None)
    # metadata: AssetMetadata = AssetMetadata(asset=clairee_asset, rig_hash='47583646ad68', animation_hash_dict={})
    print(metadata)
    print(metadata.metadata_path)
    metadata.save()
    loaded_metadata = load_asset_metadata(metadata_path=metadata.metadata_path)
    print(loaded_metadata)
    print(get_project_definition(metadata.metadata_path))
