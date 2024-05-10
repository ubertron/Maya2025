from enum import Enum, unique, auto


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
    character = auto()
    environment = auto()
    fx = auto()
    prop = auto()
    vehicle = auto()


class FileExtension(Enum):
    jpg = ".jpg"
    fbx = ".fbx"
    json = ".json"
    mb = ".mb"
    ma = ".ma"
    png = ".png"
    psd = ".psd"
    py = ".py"
    substance = ".substance"
    tga = ".tga"
    uasset = ".uasset"
    ztool = ".ztool"


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
    lambert = auto()
    materialInfo = auto()
    mesh = auto()
    nodeGraphEditorInfo = auto()
    script = auto()
    shadingEngine = auto()
    transform = auto()
