from enum import Enum, unique, auto
from dataclasses import dataclass, fields


class Axis(Enum):
    x = 0
    y = 1
    z = 2


class ComponentType(Enum):
    vertex = 'vertex'
    edge = 'edge'
    face = 'face'
    object = 'object'
    vertex_face = 'vertex face'
    element = 'element'
    uv = 'uv'


class Gender:
    male = auto()
    female = auto()
    other = auto()
    none = auto()


class AssetType(Enum):
    character = 'Characters'
    environment = 'Environments'
    fx = 'FX'
    prop = 'Props'
    vehicle = 'Vehicles'

    @staticmethod
    def keys() -> list:
        return list(map(lambda x: x.name, AssetType))

    @staticmethod
    def values() -> list:
        return list(map(lambda x: x.value, AssetType))

    @staticmethod
    def get(key: str):
        return AssetType.__members__[key]


if __name__ == '__main__':
    print(AssetType.names(), AssetType.values())
    print(AssetType.get('character'))
    # print(type(AssetType.get('character')))
    # print(type(AssetType.list()[0]))


class FileExtension(Enum):
    ams = '.ams'
    jpg = '.jpg'
    fbx = '.fbx'
    json = '.json'
    mb = '.mb'
    ma = '.ma'
    png = '.png'
    psd = '.psd'
    py = '.py'
    substance = '.substance'
    tga = '.tga'
    uasset = '.uasset'
    ztool = '.ztool'


@unique
class Alignment(Enum):
    horizontal = auto()
    vertical = auto()


@unique
class SoftwarePlatform(Enum):
    Houdini = auto()
    Maya = auto()
    Photoshop = auto()
    Standalone = auto()
    Substance = auto()
    Unreal = auto()


@unique
class Gender(Enum):
    male = auto()
    female = auto()
    other = auto()


@unique
class ObjectType(Enum):
    file = auto()
    lambert = auto()
    materialInfo = auto()
    mesh = auto()
    nodeGraphEditorInfo = auto()
    modelPanel = auto()
    nurbsCurve = auto()
    place2dTexture = auto()
    script = auto()
    shadingEngine = auto()
    transform = auto()


class Attr(Enum):
    translate = '.translate'
    rotate = '.rotate'
    scale = '.scale'


@unique
class DataType(Enum):
    float = auto()
    float2 = auto()
    float3 = auto()
    int = auto()
    int2 = auto()
    int3 = auto()
    long = auto()
    long2 = auto()
    long3 = auto()
    double = auto()
    double2 = auto()
    double3 = auto()
    str = auto()
    list = auto()


@unique
class Engine(Enum):
    godot = 'Godot'
    python = 'Python'
    spark = 'Spark AR'
    standalone = 'Standalone'
    unity = 'Unity'
    unreal = 'Unreal Engine'


@dataclass
class Platform:
    engine: Engine
    version: str or None

    def __repr__(self) -> str:
        return f'{self.engine.value} v{self.version}' if self.version else f'{self.engine.value}'


@unique
class ResourceType(Enum):
    animation = auto()
    image = auto()
    metadata = auto()
    rig = auto()
    scene = auto()


@unique
class MetadataKey(Enum):
    project = auto()
    name = auto()
    asset_type = auto()
    asset_schema = auto()
    export_hash = auto()
    animations = auto()



