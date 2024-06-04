import json

from dataclasses import dataclass
from pathlib import Path

from core.core_enums import AssetType, FileExtension, MetadataKey
from maya_tools.ams.asset import Asset
from maya_tools.ams.project_utils import ProjectDefinition, load_project_definition


@dataclass
class AssetMetadata:
    asset: Asset
    export_hash: str
    animation_hash_dict: dict or None

    def __repr__(self) -> str:
        return json.dumps(self.data_dict, indent=4)

    def export(self):
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
            MetadataKey.project.name: self.asset.project.name,
            MetadataKey.name.name: self.asset.name,
            MetadataKey.asset_type.name: self.asset.asset_type.name,
            MetadataKey.schema.name: self.asset.schema if self.asset.schema else None,
            MetadataKey.source_art_folder.name: self.asset.source_art_folder_relative.as_posix(),
            MetadataKey.export_folder.name: self.asset.export_folder_relative.as_posix(),
            MetadataKey.export_hash.name: self.export_hash,
            MetadataKey.animations.name: self.animation_hash_dict if self.animation_hash_dict else None
        }


def load_asset_metadata(metadata_path: Path, project: ProjectDefinition) -> AssetMetadata or None:
    """
    Get the AssetMetadata instance from the metadata path if it exists
    :param metadata_path:
    :param project:
    :return:
    """
    if metadata_path.exists():
        with open(metadata_path.as_posix()) as f:
            asset_metadata = json.load(f)

        name = asset_metadata[MetadataKey.name.name]
        asset_type = AssetType.__members__[asset_metadata[MetadataKey.asset_type.name]]
        schema = asset_metadata[MetadataKey.schema.name]
        asset = Asset(name=name, asset_type=asset_type, project=project, schema=schema)
        export_hash = asset_metadata[MetadataKey.export_hash.name]
        animation_hash_dict = asset_metadata[MetadataKey.animations.name]
        project_def = load_project_definition(asset_metadata[MetadataKey.project_root.name])

        return AssetMetadata(asset=asset, export_hash=export_hash, animation_hash_dict=animation_hash_dict, project=project_def)


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
    metadata: AssetMetadata = AssetMetadata(asset=clairee_asset, export_hash='47583646ad68', animation_hash_dict=data_dict)
    # metadata: AssetMetadata = AssetMetadata(asset=clairee_asset, export_hash='47583646ad68', animation_hash_dict={})
    print(metadata)
    metadata.export()
    print(metadata.metadata_path)
