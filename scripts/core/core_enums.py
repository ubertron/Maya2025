from __future__ import annotations

from enum import Enum, unique, auto
from dataclasses import dataclass


@unique
class Alignment(Enum):
    horizontal = auto()
    vertical = auto()


class AssetType(Enum):
    character = 'Characters'
    environment = 'Environments'
    fx = 'FX'
    prop = 'Props'
    vehicle = 'Vehicles“'

    @staticmethod
    def keys() -> list:
        return [x.name for x in AssetType]

    @staticmethod
    def values() -> list[str]:
        return [x.value for x in AssetType]

    @staticmethod
    def get_by_key(key: str):
        return AssetType[key]


class Attributes(Enum):
    translate = '.translate'
    rotate = '.rotate'
    scale = '.scale'


class Axis(Enum):
    x = 0
    y = 1
    z = 2

    @staticmethod
    def get_by_value(value: int) -> Enum:
        return next((x for x in list(map(lambda x: x, Axis)) if x.value == value), None)

    @staticmethod
    def get_by_key(key: str) -> Enum or None:
        return Axis(key)


class ComponentType(Enum):
    cv = 'control vertex'
    edge = 'edge'
    element = 'element'
    face = 'face'
    locator = 'locator'
    object = 'object'
    uv = 'uv'
    vertex = 'vertex'
    vertex_face = 'vertex face'


class CustomType(Enum):
    boxy = auto()
    door = auto()
    staircase = auto()
    window = auto()


@unique
class DataType(Enum):
    enum = auto()
    double = auto()
    double2 = auto()
    double3 = auto()
    float = auto()
    float2 = auto()
    float3 = auto()
    int = auto()
    int2 = auto()
    int3 = auto()
    list = auto()
    long = auto()
    long2 = auto()
    long3 = auto()
    message = auto()
    string = auto()


@unique
class Engine(Enum):
    godot = 'Godot'
    python = 'Python'
    spark = 'Spark AR'
    standalone = 'Standalone'
    unity = 'Unity'
    unreal = 'Unreal Engine'


@unique
class Gender(Enum):
    male = auto()
    female = auto()
    other = auto()
    none = auto()


class FileExtension(Enum):
    ams = '.ams'
    jpg = '.jpg'
    fbx = '.fbx'
    json = '.json'
    mb = '.mb'
    ma = '.ma'
    obj = '.obj'
    png = '.png'
    psd = '.psd'
    py = '.py'
    substance = '.substance'
    tga = '.tga'
    uasset = '.uasset'
    ztool = '.ztool'


@unique
class Language(Enum):
    """Enum for language."""

    mel = auto()
    python = auto()


@unique
class MetadataKey(Enum):
    """Enum for metadata."""

    project = auto()
    name = auto()
    asset_type = auto()
    schema = auto()
    source_art_folder = auto()
    export_folder = auto()
    rig_hash = auto()
    animations = auto()


@unique
class ModifierKey(Enum):
    """Enum for modifier keys."""

    alt = auto()
    control = auto()
    command = auto()


class OperatingSystem(Enum):
    linux = 'Linux'
    mac = 'Darwin'
    windows = 'Windows'

    @staticmethod
    def get_by_value(value: str) -> Enum:
        return next((x for x in OperatingSystem if x.value == value), None)


@unique
class ToolState(Enum):
    open = auto()
    closed = auto()


@unique
class Position(Enum):
    minimum = 'Minimum'
    center = 'Center'
    maximum = 'Maximum'

    @staticmethod
    def items() -> list:
        return [x for x in Position]

    @staticmethod
    def keys() -> list:
        return [x.name for x in Position]

    @staticmethod
    def values() -> list:
        return [x.value for x in Position]

    @staticmethod
    def get_by_key(key: str) -> Enum or None:
        return Position[key]

    @staticmethod
    def get_by_value(value: str) -> Enum:
        return Position(value)


@dataclass
class Platform:
    engine: Engine
    version: str or None

    def __repr__(self) -> str:
        return f'{self.engine.value} v{self.version}' if self.version else f'{self.engine.value}'


@unique
class PythonPlatform(Enum):
    maya = 'maya'
    standalone = 'python'
    unreal = 'unrealeditor'

    @staticmethod
    def get_by_value(value: str) -> Enum:
        return PythonPlatform(value)


@unique
class ResourceType(Enum):
    animation = auto()
    image = auto()
    metadata = auto()
    rig = auto()
    scene = auto()


class Side(Enum):
    left = auto()
    right = auto()
    center = auto()
    top = auto()
    bottom = auto()
    front = auto()
    back = auto()


@unique
class SoftwarePlatform(Enum):
    Houdini = auto()
    Maya = auto()
    Photoshop = auto()
    Standalone = auto()
    Substance = auto()
    Unreal = auto()


class SurfaceDirection(Enum):
    concave = auto()
    convex = auto()


@unique
class Unit(Enum):
    millimeter = "mm"
    centimeter = "cm"
    meter = "m"
    kilometer = "km"
    inch = "in"
    foot = "ft"
    yard = "yd"
    mile = "mi"


@unique
class WidgetMode(Enum):
    classic = auto()
    maya_floating_window = auto()


if __name__ == '__main__':
    # my_enum = MetadataKey.rig_hash
    # print(isinstance(my_enum, MetadataKey))
    # print(type(my_enum))
    # print(Position.get_by_value('Center'))
    # print(Position.get_by_key('Center'))
    # print(Position.items())
    print(Axis["x"])
    print(Axis(2))