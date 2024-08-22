from enum import unique, Enum, auto


@unique
class FBXProperty(Enum):
    FBXExportAnimationOnly = auto()  # bool
    FBXExportApplyConstantKeyReducer = auto()  # bool
    FBXExportAxisConversionMethod = auto()  # [none|convertAnimation|addFbxRoot]
    FBXExportBakeComplexAnimation = auto()  # bool
    FBXExportBakeComplexEnd = auto()  # int
    FBXExportBakeComplexStart = auto()  # int
    FBXExportBakeComplexStep = auto()  # int
    FBXExportBakeResampleAnimation = auto()  # bool
    FBXExportCacheFile = auto()  # bool
    FBXExportCameras = auto()  # bool
    FBXExportColladaFrameRate = auto()  # float
    FBXExportColladaSingleMatrix = auto()  # bool
    FBXExportColladaTriangulate = auto()  # bool
    FBXExportConstraints = auto()  # bool
    FBXExportConvertUnitString = auto()  # [mm|dm|cm|m|km|In|ft|yd|mi]
    FBXExportDxfTriangulate = auto()  # bool
    FBXExportDxfDeformation = auto()  # bool
    FBXExportEmbeddedTextures = auto()  # bool
    FBXExportFileVersion = auto()  # -v [version]
    FBXExportGenerateLog = auto()  # bool
    FBXExportHardEdges = auto()  # bool
    FBXExportInAscii = auto()  # bool
    FBXExportIncludeChildren = auto()  # bool
    FBXExportInputConnections = auto()  # bool
    FBXExportInstances = auto()  # bool
    FBXExportLights = auto()  # bool
    FBXExportQuaternion = auto()  # bool
    FBXExportQuickSelectSetAsCache = auto()  # -v "setName"
    FBXExportReferencedAssetsContent = auto()  # bool
    FBXExportScaleFactor = auto()  # float
    FBXExportShapes = auto()  # bool
    FBXExportSkeletonDefinitions = auto()  # bool
    FBXExportSkins = auto()  # bool
    FBXExportSmoothingGroups = auto()  # bool
    FBXExportSmoothMesh = auto()  # bool
    FBXExportSplitAnimationIntoTakes = auto()  # -v \"take_name\" 1 5 (see documentation)
    FBXExportTangents = auto()  # bool
    FBXExportTriangulate = auto()  # bool
    FBXExportUpAxis = auto()  # [y|z]
    FBXExportUseSceneName = auto()  # bool


class LayerDisplayType(Enum):
    normal = 0
    template = 1
    reference = 2

    @staticmethod
    def get_by_value(value: int):
        return next(x for x in list(map(lambda x: x, LayerDisplayType)) if x.value == value)


@unique
class ObjectType(Enum):
    animCurve = auto()
    joint = auto()
    file = auto()
    lambert = auto()
    locator = auto()
    materialInfo = auto()
    mesh = auto()
    nodeGraphEditorInfo = auto()
    modelPanel = auto()
    nurbsCurve = auto()
    place2dTexture = auto()
    script = auto()
    shadingEngine = auto()
    transform = auto()


if __name__ == '__main__':
    print(LayerDisplayType.get_by_value(0))
