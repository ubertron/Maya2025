import logging

from maya import cmds
from pathlib import Path
from typing import Optional

from maya_tools.maya_enums import LayerDisplayType
from maya_tools.ams.asset import Asset
from maya_tools.ams.asset_metadata import AssetMetadata, load_asset_metadata
from maya_tools.ams.rig_utils import generate_rig_hash
from maya_tools.ams.resource import Resource
from maya_tools.animation_utils import get_keyframe_range
from maya_tools.io.fbx_utils import export_fbx
from maya_tools.io.fbx_presets import RigExportPreset, AnimationExportPreset, FBXPreset
from maya_tools.scene_utils import load_scene, get_scene_path, save_scene
from maya_tools import layer_utils


def export_rig(asset: Asset):
    """
    Export the rig component of an Asset
    :param asset:
    """
    export_asset(asset=asset, scene_file_path=asset.scene_file_path, export_file_path=asset.scene_file_export_path,
                 export_preset=RigExportPreset(), nodes=[asset.rig_group_node, asset.geometry_group_node])

    # create/update asset metadata
    rig_hash: str = generate_rig_hash(asset=asset)
    # thumbnail = generate_thumbnail(asset)

    if asset.metadata_path.exists():
        asset_metadata = load_asset_metadata(metadata_path=asset.metadata_path)
        asset_metadata.rig_hash = rig_hash
    else:
        asset_metadata = AssetMetadata(asset=asset, rig_hash=rig_hash, animation_hash_dict={})

    asset_metadata.save()
    logging.info(f'Metadata saved to {asset_metadata.metadata_path}')
    # export complete


def export_animation(asset: Asset, resource: Resource):
    # export
    scene_file_path = asset.source_art_folder.joinpath(resource.scene_file_name)
    export_file_path = asset.get_animation_export_path(animation_name=resource.name)

    # need to open scene if not open to get the frame range
    if get_scene_path() != scene_file_path:
        load_scene(scene_file_path)

    keyframe_range = get_keyframe_range(asset.motion_system_group_node)
    export_preset = AnimationExportPreset(start_end=keyframe_range)
    export_asset(asset=asset, scene_file_path=scene_file_path, export_file_path=export_file_path,
                 export_preset=export_preset, nodes=[asset.rig_group_node])

    # update asset metadata
    rig_hash: str = generate_rig_hash(asset=asset)
    asset_metadata: AssetMetadata = load_asset_metadata(metadata_path=asset.metadata_path)
    asset_metadata.animation_hash_dict[resource.name] = rig_hash
    asset_metadata.save()
    logging.info(f'Metadata updated: {asset_metadata.metadata_path}')
    # export complete


def export_asset(asset: Asset, scene_file_path: Path, export_file_path: Path, export_preset: FBXPreset,
                 nodes: Optional[list[str]] = None, auto_save: bool = False):
    """
    Function exports an asset to specified export location
    :param asset:
    :param scene_file_path:
    :param export_file_path:
    :param export_preset:
    :param auto_save:
    :param nodes:
    """
    for node in nodes:
        assert cmds.objExists(node), f'Cannot find node: {node}. Aborting export.'

    # save file
    if auto_save:
        save_scene(force=True)

    # Perforce-only: check in scene and check out export file

    # set layer display types to normal
    layer_display_types = layer_utils.get_layer_display_types(custom_only=True)

    for layer in layer_display_types.keys():
        layer_utils.set_layer_display_type(layer=layer, layer_display_type=LayerDisplayType.normal)

    # export asset
    export_preset.activate()
    asset.export_folder.mkdir(parents=True, exist_ok=True)

    if nodes:
        cmds.select(nodes)

    export_fbx(export_path=export_file_path, selected=nodes is not None)

    # Perforce-only: add export file if not already added

    # restore layer display types
    for layer, value in layer_display_types.items():
        layer_utils.set_layer_display_type(layer=layer, layer_display_type=value)

    logging.info(f'Asset exported to {export_file_path}')





