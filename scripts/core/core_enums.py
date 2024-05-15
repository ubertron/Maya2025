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
    file = auto()
    lambert = auto()
    materialInfo = auto()
    mesh = auto()
    nodeGraphEditorInfo = auto()
    modelPanel = auto()
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
