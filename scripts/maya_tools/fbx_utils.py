import logging

from pathlib import Path
from maya import cmds, mel

from maya_tools.maya_environment_utils import MAYA_APP_DIR

FBX_EXPORT_PRESETS: Path = [x for x in MAYA_APP_DIR.joinpath('FBX').rglob('*.fbxexportpreset')]


def load_fbx_preset(preset_path: Path):
    """
    Loads an FBX preset file
    """
    assert preset_path.exists(), f'Cannot find preset: {preset_path.as_posix()}'
    command = f'FBXLoadExportPresetFile -f "{preset_path.as_posix()}";'
    logging.info(command)
    mel.eval(command)


def export_fbx(export_path: Path, selected=True):
    """
    Export fbx
    :param export_path:
    :param selected:
    """
    command = f'FBXExport -f "{export_path.as_posix()}"{" -s" if selected else ""}'
    logging.info(command)
    mel.eval(command)


def get_fbx_properties():
    """
    List all the FBX properties
    """
    return mel.eval('FBXProperties;')


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


def set_export_frame_range(start: int, end: int):
    """
    Set the export frame range
    :param start:
    :param end:
    """
    mel.eval(f'FBXExportBakeComplexStart -v {start}')
    mel.eval(f'FBXExportBakeComplexEnd -v {end}')


def get_fbx_export_preset_path(preset_name: str, single: bool = True) -> Path or list:
    """
    Finds the path of an FBX export preset
    :param preset_name:
    :param single:
    :return:
    """
    result = [x for x in FBX_EXPORT_PRESETS if x.stem == preset_name]

    if single:
        assert len(result) == 1, f'Warning: multiple presets found for {preset_name}'

    return result[0] if len(result) == 1 else result


FBX_EXPORT_PRESET_RIG: Path = get_fbx_export_preset_path('ams_rig', single=True)
FBX_EXPORT_PRESET_ANIMATION: Path = get_fbx_export_preset_path('ams_animation', single=True)
