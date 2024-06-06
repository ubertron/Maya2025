from abc import ABC, abstractmethod
from maya_tools.ams.asset import Asset
from maya_tools.ams.validation.test_result import TestResult


class AssetTest(ABC):
    @classmethod
    @abstractmethod
    def get_asset_types(cls):
        pass

    @classmethod
    @abstractmethod
    def test(cls, asset: Asset) -> TestResult:
        pass
