import logging

from maya import cmds, mel

from maya_tools.maya_enums import LayerDisplayType
from maya_tools.ams.asset import Asset
from maya_tools.ams.asset_metadata import AssetMetadata, load_asset_metadata
from maya_tools.ams.project_utils import get_project_definition
from maya_tools.ams.rig_utils import generate_rig_hash
from maya_tools.ams.validation.tests.asset_structure import AssetStructure
from maya_tools.fbx_utils import export_fbx
from maya_tools.fbx_preset import RigExportPreset
from maya_tools.scene_utils import load_scene, get_scene_path
from maya_tools import layer_utils


def export_rig(asset: Asset):
    """
    Export the rig component of an Asset
    :param asset:
    """
    if get_scene_path() != asset.scene_file_path:
        load_scene(asset.scene_file_path)

    assert cmds.objExists(asset.rig_group_node), 'Cannot find rig group node'
    assert cmds.objExists(asset.geometry_group_node), 'Cannot find geometry group node'
    valid = validate_character(asset=asset)
    assert valid is True, 'Rig failed validation, aborting export'

    # save file
    # Perforce-only: check in

    RigExportPreset().activate()
    cmds.select(asset.rig_group_node, asset.geometry_group_node)
    asset.scene_file_export_path.parent.mkdir(parents=True, exist_ok=True)

    # get layer display types
    layer_display_types = layer_utils.get_layer_display_types(custom_only=True)

    # set layer display types to normal
    for layer in layer_display_types.keys():
        layer_utils.set_layer_display_type(layer=layer, layer_display_type=LayerDisplayType.normal)

    # Perforce-only: check out export file

    # export rig
    export_fbx(export_path=asset.scene_file_export_path, selected=True)

    # restore layer display types
    for layer, value in layer_display_types.items():
        layer_utils.set_layer_display_type(layer=layer, layer_display_type=value)

    logging.info(f'Rig exported to {asset.scene_file_export_path}')

    # Asset Metadata
    export_hash: str = generate_rig_hash(asset=asset)
    # thumbnail = generate_thumbnail(asset)
    if asset.metadata_path.exists():
        asset_metadata = load_asset_metadata(metadata_path=asset.metadata_path, project=get_project_definition())
    else:
        asset_metadata = AssetMetadata()

    # export complete


def validate_character(asset: Asset) -> bool:
    """
    Run the tests for characters
    :param asset:
    :return:
    """
    logging.info(f'Validating {asset.name}')
    test_result: TestResult = AssetStructure().test(asset)
    logging.info(f'Tests passed? {test_result.passed}')

    return test_result.passed
