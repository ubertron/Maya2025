from typing import Optional, Sequence

from maya_tools.io.fbx_preset import FBXPreset
from maya_tools.maya_enums import FBXProperty


class RigExportPreset(FBXPreset):
    fbx_properties = {
        FBXProperty.FBXExportSmoothingGroups: True,
        FBXProperty.FBXExportTangents: True,
        FBXProperty.FBXExportTriangulate: True,
        FBXProperty.FBXExportColladaFrameRate: 25.0,
        FBXProperty.FBXExportConstraints: True,
        FBXProperty.FBXExportInputConnections: False,
        FBXProperty.FBXExportCameras: False,
        FBXProperty.FBXExportLights: False,
        FBXProperty.FBXExportGenerateLog: False,
    }

    custom_properties = {
        'Export|IncludeGrp|Animation': '0',
    }

    def __init__(self):
        super(RigExportPreset, self).__init__(self.fbx_properties, self.custom_properties)


class AnimationExportPreset(FBXPreset):
    fbx_properties = {
        FBXProperty.FBXExportBakeComplexAnimation: True,
        FBXProperty.FBXExportBakeComplexStart: 1,
        FBXProperty.FBXExportBakeComplexEnd: 100,
        FBXProperty.FBXExportColladaFrameRate: 25.0,
        FBXProperty.FBXExportInputConnections: False,
        FBXProperty.FBXExportCameras: False,
        FBXProperty.FBXExportLights: False,
    }
    custom_properties = {
        'Export|AdvOptGrp|UI|ShowWarningsManager': '0'
    }

    def __init__(self, start_end: Optional[Sequence[float]] = None):
        super(AnimationExportPreset, self).__init__(self.fbx_properties, self.custom_properties)

        if start_end and len(start_end) == 2:
            start, end = start_end
            self.fbx_properties[FBXProperty.FBXExportBakeComplexStart] = int(start)
            self.fbx_properties[FBXProperty.FBXExportBakeComplexEnd] = int(end)
