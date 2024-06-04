import logging

from maya import mel
from typing import Optional, Sequence

from maya_tools.fbx_utils import set_export_frame_range, check_fbx_plug_in, fbx_reset_export, \
    set_fbx_property, get_fbx_property
from maya_tools.maya_enums import FBXProperty


class FBXPreset:
    fbx_property_tag = 'FBXProperty'

    def __init__(self, fbx_properties: Optional[dict] = None, custom_properties: Optional[dict] = None):
        """
        Presets for FBX export
        Note: these are not to be confused with the FBX Export Presets which are saved in the maya_app_dir
        @param fbx_properties: properties defined in the FBXProperty enum
        @param custom_properties: properties listed in mel.other.FBXProperties()
        """
        self.fbx_properties = fbx_properties if fbx_properties else {}
        self.custom_properties = custom_properties if custom_properties else {}

    def activate(self):
        """
        Apply the settings of an FBX preset
        """
        fbx_reset_export()

        for fbx_property, value in self.fbx_properties.items():
            set_fbx_property(fbx_property=fbx_property, value=value)

        for custom_property, value in self.custom_properties.items():
            mel.eval(f'{self.fbx_property_tag} {custom_property} -v {value};')

    def query_current(self):
        """
        Get the corresponding values in Maya for the properties in the current preset
        """
        logging.info('\nCurrent FBX Property values')

        for fbx_property in self.fbx_properties.keys():
            value = mel.eval(f'{fbx_property.name} -q;')
            logging.info(f'{fbx_property.name}: {value}')

        for custom_property in self.custom_properties:
            value = mel.eval(f'{self.fbx_property_tag} {custom_property} -q;')
            logging.info(f'{custom_property}: {value}')

    def query_preset(self):
        """
        Get the property values of this preset
        """
        logging.info('\nPreset FBX Property values')

        for fbx_property, value in self.fbx_properties.items():
            logging.info(f'{fbx_property.name}: {value}')

        for custom_property, value in self.custom_properties.items():
            logging.info(f'{custom_property}: {value}')

    def compare_properties(self):
        """
        Compare the property values of the preset with the corresponding values of the current system
        This is a way to see how a preset compares to the default values
        Useful when used in conjunction with fbx_utils.fbx_reset_export()
        Note that some boolean properties seem to be either 1|0 or true|false - inconsistency
        """
        logging.info('Compare FBX Properties')

        diff_count = []

        for key, value in self.fbx_properties.items():
            maya_value = get_fbx_property(fbx_property=key, output=False)

            if type(value) is bool:
                if key is FBXProperty.FBXExportBakeComplexAnimation:
                    value = str(value).lower()
                else:
                    value = '1' if value is True else '0'

            diff = ' | DIFF' if str(maya_value) != str(value) else None
            diff_count.append(diff)
            logging.info(f'Property: {key.name} | system value: {maya_value} | preset value: {value}{diff}')

        for key, value in self.custom_properties.items():
            maya_value = mel.eval(f'{self.fbx_property_tag} {key} -q;')

            if type(value) is bool:
                value = '1' if value is True else '0'

            diff = ' | DIFF' if str(maya_value) != str(value) else ''
            diff_count.append(diff)
            logging.info(f'Property: {key} | system value: {maya_value} | preset value: {value}{diff}')

        if None in diff_count:
            logging.info('Warning: Default values found')
        else:
            logging.info('All properties are exclusive from default values')


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
        FBXProperty.FBXExportBakeComplexStart: 1.0,
        FBXProperty.FBXExportBakeComplexEnd: 100.0,
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
            self.fbx_properties[FBXProperty.FBXExportBakeComplexStart] = start
            self.fbx_properties[FBXProperty.FBXExportBakeComplexEnd] = end
