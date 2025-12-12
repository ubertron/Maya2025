"""ams_enums.py"""
from enum import Enum, auto, unique


@unique
class AssetType(Enum):
    animation = "Animations"
    audio = "Audio"
    character = "Characters"
    environment = "Environments"
    fx = "FX"
    material = "Materials"
    prop = "Props"
    scene = "Scenes"
    texture = "Textures"
    vehicle = "Vehicles"
    ui = "UI"

    @staticmethod
    def engine_exclusive() -> list:
        return [AssetType.scene, AssetType.ui]

    @staticmethod
    def geometry_types() -> list:
        return [AssetType.character, AssetType.environment, AssetType.prop, AssetType.vehicle]

    @staticmethod
    def names() -> list:
        return [x.name for x in AssetType]


if __name__ == "__main__":
    print(AssetType.geometry_types())
