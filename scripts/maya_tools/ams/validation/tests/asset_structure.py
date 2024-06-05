import logging

from maya import cmds

from maya_tools.ams.validation.asset_test import AssetTest
from maya_tools.ams.validation.test_result import TestResult
from maya_tools.ams.asset import Asset
from core.core_enums import AssetType


class AssetStructure(AssetTest):
    @classmethod
    def get_asset_types(cls) -> list[AssetType]:
        return [AssetType.character, AssetType.environment, AssetType.vehicle, AssetType.prop]

    @classmethod
    def test(cls, asset: Asset) -> TestResult:
        """
        Check presence of vital nodes in the asset hierarchy
        :param asset:
        :return:
        """
        test_result = TestResult()

        if not cmds.objExists(asset.asset_root_node):
            test_result.add_failure('Root node not found')

        if not cmds.objExists(asset.rig_group_node):
            test_result.add_failure('Rig group node not found')

        if not cmds.objExists(asset.face_group_node):
            test_result.add_failure('Face group node not found')

        if not cmds.objExists(asset.motion_system_group_node):
            test_result.add_failure('Motion system node not found')

        if not cmds.objExists(asset.geometry_group_node):
            test_result.add_failure('Geometry group node not found')

        if len(test_result.failure_list):
            test_result.set_fix_script(cls.fix_script)

        return test_result

    @classmethod
    def fix_script(cls):
        logging.info('Please consult asset documentation')
