from maya_tools.ams.asset import Asset
from maya_tools.ams.validation.asset_test import AssetTest
from maya_tools.ams.validation.test_result import TestResult
from core.core_enums import AssetType


def run_test_suite(asset: Asset) -> list[TestResult]:
    """
    Runs all the relevant tests for an AssetType on an asset
    :param asset:
    :return:
    """
    asset_tests = collect_tests_by_asset_type(asset.asset_type)
    test_results: list[TestResult] = []

    for asset_test in asset_tests:
        test_results.append(asset_test.test(asset))

    return test_results


def collect_tests_by_asset_type(asset_type: AssetType) -> list[AssetTest]:
    """
    Look through all the tests in the tests folder and return a list of tests for the passed AssetType
    :param asset_type:
    """
    return []
