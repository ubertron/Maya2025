import logging

from maya import cmds

from maya_tools.ams.validation.asset_test import AssetTest
from maya_tools.ams.validation.test_result import TestResult
from maya_tools.ams.rig_utils import generate_rig_hash
from maya_tools.ams.asset import Asset
from maya_tools.ams.asset_metadata import load_asset_metadata, AssetMetadata
from maya_tools.scene_utils import get_scene_name
from core.core_enums import AssetType


class LatestRig(AssetTest):
    @classmethod
    def get_asset_types(cls) -> list[AssetType]:
        return [AssetType.character, AssetType.vehicle, AssetType.prop]

    @classmethod
    def test(cls, asset: Asset) -> TestResult:
        """
        If asset is an animation scene, check the rig hash against the metadata
        Do not need to check the rig scene itself as that one defines the latest
        :param asset:
        :return:
        """
        cls.asset = asset
        test_result = TestResult()

        if get_scene_name(include_extension=False) in asset.animations:
            rig_hash = generate_rig_hash(asset)
            metadata: AssetMetadata = load_asset_metadata(asset.metadata_path)

            if rig_hash != metadata.rig_hash:
                test_result.add_failure('Rig does not match with latest')
                test_result.set_fix_script(cls.fix_script)

        return test_result

    @classmethod
    def fix_script(cls):
        logging.info(f'Update {cls.asset.name} to latest rig')
