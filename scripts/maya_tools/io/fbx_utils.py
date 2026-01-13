import logging
import os

from pathlib import Path
from maya import cmds, mel
from typing import Union

from core import logging_utils
from maya_tools.maya_enums import FBXProperty
from maya_tools.maya_environment_utils import MAYA_APP_DIR

FBX_PLUG_IN: str = 'fbxmaya.mll'
FBX_PLUG_IN_PATH: Path = Path(cmds.pluginInfo(FBX_PLUG_IN, query=True, path=True))
FBX_EXPORT_PRESETS: list[Path] = [x for x in MAYA_APP_DIR.joinpath('FBX').rglob('*.fbxexportpreset')]
LOGGER = logging_utils.get_logger(__name__, level=logging.DEBUG)

def export_fbx(export_path: Path, selected: bool = True, replace: bool = True):
    """
    Export fbx
    :param export_path:
    :param selected:
    :param replace:
    :return: Path
    """
    if replace and export_path.exists():
        os.remove(export_path.as_posix())

    export_path.parent.mkdir(parents=True, exist_ok=True)
    command = f'FBXExport -f "{export_path.as_posix()}"{" -s" if selected else ""};'
    logging.info(command)
    mel.eval(command)


def get_fbx_properties():
    """
    List all the FBX properties
    """
    return mel.eval('FBXProperties;')


def fbx_reset_export():
    """
    Reset the FBX export settings
    Needs to be done prior to setting the values in an FBXPreset
    """
    mel.eval('FBXResetExport;')


def get_export_frame_range() -> tuple or False:
    """
    Get the export frame range
    :return:
    """
    result = mel.eval('FBXExportBakeComplexAnimation -q;')

    if result == 'true':
        return mel.eval('FBXExportBakeComplexStart -q;'), mel.eval('FBXExportBakeComplexEnd -q;')
    else:
        return False


def load_fbx_preset(preset_path: Path):
    """
    Loads a Maya-style FBX preset file
    """
    assert preset_path.exists(), f'Cannot find preset: {preset_path.as_posix()}'
    command = f'FBXLoadExportPresetFile -f "{preset_path.as_posix()}";'
    logging.info(command)
    mel.eval(command)


def get_fbx_export_preset_path(preset_name: str, single: bool = True) -> Path or list:
    """
    Finds the path of an FBX export preset
    :param preset_name:
    :param single:
    :return:
    """
    result = [x for x in FBX_EXPORT_PRESETS if x.stem == preset_name]

    if single:
        paths = "\n".join(x.as_posix() for x in result)
        assert len(result) == 1, f'Warning: multiple presets found for {preset_name}\n{paths}'
        return result[0]

    return result[0] if len(result) == 1 else result


def get_fbx_animation_preset() -> Path:
    return get_fbx_export_preset_path('ams_animation', single=True)


def get_fbx_rig_preset() -> Path:
    return get_fbx_export_preset_path('ams_rig', single=True)


def check_fbx_plug_in():
    """
    Ensure that the FBX plug-in is loaded
    """
    if FBX_PLUG_IN not in cmds.pluginInfo(query=True, listPlugins=True):
        cmds.loadPlugin(FBX_PLUG_IN)
        cmds.pluginInfo(FBX_PLUG_IN, edit=True, autoload=True)


def get_fbx_property(fbx_property: FBXProperty, output: bool = False):
    """
    Get the value of an FBXProperty
    :param fbx_property:
    :param output:
    :return:
    """
    result = mel.eval(f'{fbx_property.name} -q;')

    if output:
        logging.info(result)

    return result


def set_export_frame_range(start: float, end: float):
    """
    Set the export frame range
    :param start:
    :param end:
    """
    mel.eval(f'FBXExportBakeComplexStart -v {start}')
    mel.eval(f'FBXExportBakeComplexEnd -v {end}')


def set_fbx_property(fbx_property: FBXProperty, value: Union[int, bool, float, str]):
    """
    Set the value of an FBXProperty
    :param fbx_property:
    :param value:
    """
    if type(value) is int:
        mel.eval(f'{fbx_property.name} -v {str(value).lower()};')
    elif type(value) is bool:
        if fbx_property is FBXProperty.FBXExportBakeComplexAnimation:
            mel.eval(f'{fbx_property.name} -v {str(value).lower()};')
        else:
            mel.eval(f'{fbx_property.name} -v {"1" if value is True else "0"};')
    else:
        mel.eval(f'{fbx_property.name} {value};')
