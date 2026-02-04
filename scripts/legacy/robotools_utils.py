# Robotools version 0.3: New version of Robotools for Maya 2025
import logging

from distutils.dir_util import copy_tree
from pathlib import Path
from maya import cmds

from core.core_paths import image_path, PRESETS_DIR
from core.config_utils import MayaConfig
from maya_tools import plug_in_utils
from maya_tools.io.fbx_utils import check_fbx_plug_in
from maya_tools.maya_environment_utils import is_using_mac_osx, MAYA_APP_DIR
from maya_tools.tool_utils import launch_script
from legacy.robotools_hotkeys import RobotoolsHotkeys
from legacy.robotools_shelf import RobotoolsShelf

MAYA_CONFIG: MayaConfig = MayaConfig()
PREFERENCES_KEY: str = 'PREFERENCES'


def setup_robotools():
    """
    Sets up Robotools
    """
    logging.info(f">>> robotools_utils.py setup script")
    setup_robotools_shelf()
    setup_plug_ins()
    setup_preferences()
    setup_presets()
    setup_hotkeys()

def setup_robotools_shelf():
    """Set up the robotools shelf."""
    logging.info('>>> Setting up Robotools shelf')
    RobotoolsShelf().create()


def setup_plug_ins():
    check_fbx_plug_in()


def setup_preferences():
    """
    Sets up Maya preferences
    """
    logging.info('>>> Setting Maya preferences')
    cmds.currentUnit(linear='centimeter')
    grid_size = MAYA_CONFIG.get(section=PREFERENCES_KEY, option='GRID_SIZE', default=100.0)
    grid_spacing = MAYA_CONFIG.get(section=PREFERENCES_KEY, option='GRID_SPACING', default=100.0)
    divisions = MAYA_CONFIG.get(section=PREFERENCES_KEY, option='DIVISIONS', default=2)
    cmds.grid(size=int(grid_size), spacing=float(grid_spacing), divisions=int(divisions))

    cmds.displayColor('gridHighlight', 1)
    cmds.displayColor('grid', 12)
    cmds.selectPref(clickDrag=True)

    if is_using_mac_osx():
        cmds.mouse(mouseButtonTracking=2)
        cmds.multiTouch(gestures=False, trackpad=1)


def setup_presets():
    """
    Set up the Robotools presets
    Includes FBX export presets
    """
    logging.info('>>> Setting Maya presets')
    copy_tree(src=PRESETS_DIR.as_posix(), dst=MAYA_APP_DIR.as_posix())


def setup_hotkeys():
    """
    Set up the Robotools hotkeys
    """
    logging.info('>>> Setting up hotkeys')
    RobotoolsHotkeys().apply()


def robotools_plug_in_path() -> Path or None:
    """
    Get the path of the robotools plug-in if it is in the plug-ins list
    :return:
    """
    plugins = plug_in_utils.list_plug_ins()

    return Path(cmds.pluginInfo(ROBOTOOLS_PLUG_IN, query=True, path=True)) if ROBOTOOLS_PLUG_IN in plugins else None


def delete_robotools():
    """
    Get rid of the shelf
    """
    logging.info('>>> Deleting Robotools shelf')
    RobotoolsShelf().delete()
