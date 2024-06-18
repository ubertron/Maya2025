# Robotools version 0.3: New version of Robotools for Maya 2025
import hashlib
import logging
import os

from distutils.dir_util import copy_tree
from pathlib import Path
from maya import cmds

from core.core_paths import SITE_PACKAGES, MAYA_INTERPRETER_PATH, MAYA_REQUIREMENTS, icon_path, PROJECT_ROOT, \
    PRESETS_FOLDER
from core.config_utils import MayaConfig
from maya_tools.io.fbx_utils import check_fbx_plug_in
from maya_tools import plug_in_utils
from maya_tools.utilities.shelf_manager import ShelfManager, message_script
from maya_tools.utilities import hotkey_manager
from maya_tools.maya_environment_utils import is_using_mac_osx, MAYA_APP_DIR

ROBOTOOLS_TITLE: str = 'Robotools'
ROBOTOOLS_VERSION = '0.3'
ROBOTOOLS_PLUG_IN = 'robotools'
ROBOTOOLS_SHELF_VERSION: str = 1.3
MAYA_CONFIG: MayaConfig = MayaConfig()
PREFERENCES_KEY: str = 'PREFERENCES'
ROBOTOOLS_HOTKEYS_NAME: str = 'Robotools_Hotkeys'
ROBOTOOLS_HOTKEYS_PATH: Path = PROJECT_ROOT.joinpath('scripts', 'startup', f'{ROBOTOOLS_HOTKEYS_NAME}.mhk')


def setup_robotools():
    """
    Sets up Robotools
    """
    logging.info(f">>> robotools_utils.py setup script")

    if False in (check_requirements_hash(), SITE_PACKAGES.exists()):
        install_requirements()
        warning_string = 'Robotools updated - please restart Maya'
        cmds.warning(warning_string)
    else:
        logging.info(">>> Tools up to date")

    setup_robotools_shelf()
    setup_plug_ins()
    setup_preferences()
    setup_presets()
    setup_hotkeys()


def setup_robotools_shelf():
    logging.info('>>> Setting up Robotools shelf')
    sm = ShelfManager(ROBOTOOLS_TITLE)
    sm.delete()
    sm.create(select=True)
    sm.delete_buttons()

    version_info = 'Robotools Shelf Version {}: {}'.format(ROBOTOOLS_SHELF_VERSION, robotools_plug_in_path())
    robonobo_icon = icon_path('robonobo_32.png')
    script_icon = icon_path('script.png')
    export_manager = 'from maya_tools.ams.ams_debug import launch_export_manager\nlaunch_export_manager()'
    root_name_toggle = 'from maya_tools.ams.ams_debug import root_name_toggle\nroot_name_toggle()'
    base_male_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("male")'
    load_base_male = 'from maya_tools.character_utils import load_base_character\nload_base_character("male")'
    base_female_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("female")'
    load_base_female = 'from maya_tools.character_utils import load_base_character\nload_base_character("female")'
    create_cube = 'from maya import cmds; cmds.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1)'
    slice_cmd = 'from maya_tools.mirror_utils import slice_geometry\nslice_geometry()'
    mirror_cmd = 'from maya_tools.mirror_utils import mirror_geometry\nmirror_geometry()'
    quadrangulate = 'from maya import cmds\ncmds.polyQuad()'
    merge_vertices = 'from maya_tools.geometry_utils import merge_vertices\nmerge_vertices()'
    select_triangles = 'from maya_tools import geometry_utils; geometry_utils.get_triangular_faces(select=True)'
    select_ngons = 'from maya_tools import geometry_utils; geometry_utils.get_ngons(select=True)'
    super_reset = 'from maya_tools import node_utils; node_utils.super_reset()'
    pivot_base = 'from maya_tools import node_utils; node_utils.pivot_to_base()'
    pivot_center = 'from maya_tools import node_utils; node_utils.pivot_to_center()'
    pivot_origin = 'from maya_tools import node_utils; node_utils.pivot_to_origin()'
    backface_culling = 'from maya_tools.geometry_utils import toggle_backface_culling\ntoggle_backface_culling()'
    toggle_xray = 'from maya_tools.geometry_utils import toggle_xray\ntoggle_xray()'
    rebuild_curve = 'from maya_tools import curve_utils; curve_utils.rebuild_closed_curve_from_selected_cv(False)'
    move_to_origin = 'from maya_tools import node_utils; node_utils.move_to_origin()'
    move_to_last = 'from maya_tools import node_utils; node_utils.move_to_last()'
    rename_nodes = 'from maya_tools import node_utils; node_utils.rename_nodes()'
    pivot_match = 'from maya_tools import node_utils; node_utils.match_pivot_to_last()'

    sm.add_label('Robotools v{}'.format(ROBOTOOLS_VERSION), bold=True)
    sm.add_shelf_button(label='About Robotools', icon=robonobo_icon, command=message_script(version_info))
    sm.add_separator()
    sm.add_label('AMS')
    sm.add_shelf_button(label='Export Manager (Debug)', overlay_label='ExMan', icon=script_icon, command=export_manager)
    sm.add_shelf_button(label='Root Name Toggle (Debug)', overlay_label='RtTog', icon=script_icon, command=root_name_toggle)
    sm.add_separator()
    sm.add_label('Characters')
    sm.add_shelf_button(label='Import Base Male', icon=icon_path('base_male.png'), command=base_male_cmd)
    sm.add_shelf_button(label='Load Base Male', icon=script_icon, command=load_base_male, overlay_label='loadM')
    sm.add_shelf_button(label='Import Base Female', icon=icon_path('base_female.png'), command=base_female_cmd)
    sm.add_shelf_button(label='Load Base Female', icon=script_icon, command=load_base_female, overlay_label='loadF')
    sm.add_separator()
    sm.add_label('Geometry')
    sm.add_shelf_button(label='Create Cube', overlay_label='Cube', icon=script_icon, command=create_cube)
    sm.add_shelf_button(label='Slice', icon=icon_path('slice.png'), command=slice_cmd)
    sm.add_shelf_button(label='Mirror', icon=icon_path('mirror.png'), command=mirror_cmd)
    sm.add_shelf_button(label='Quadrangulate', overlay_label='Quad', icon=script_icon, command=quadrangulate)
    sm.add_shelf_button(label='Merge Vertices', overlay_label='Merge', icon=script_icon, command=merge_vertices)
    sm.add_shelf_button(label='Select Triangles', overlay_label='Tris', icon=script_icon, command=select_triangles)
    sm.add_shelf_button(label='Select Ngons', overlay_label='Ngons', icon=script_icon, command=select_ngons)
    sm.add_shelf_button(label='Toggle Backface Culling', overlay_label='tBFC', icon=script_icon, command=backface_culling)
    sm.add_shelf_button(label='Toggle Xray', overlay_label='tXRay', icon=script_icon, command=toggle_xray)
    sm.add_separator()
    sm.add_label('Shapes')
    sm.add_shelf_button(label='Rebuild Curve From CV', overlay_label='Rbld', icon=script_icon, command=rebuild_curve)
    sm.add_separator()
    sm.add_label('Nodes')
    sm.add_shelf_button(label='Super Reset', overlay_label='SpRst', icon=script_icon, command=super_reset)
    sm.add_shelf_button(label='Pivot To Base', overlay_label='Pv->B', icon=script_icon, command=pivot_base)
    sm.add_shelf_button(label='Pivot To Center', overlay_label='Pv->C', icon=script_icon, command=pivot_center)
    sm.add_shelf_button(label='Pivot To Origin', overlay_label='Pv->O', icon=script_icon, command=pivot_origin)
    sm.add_shelf_button(label='Move To Origin', overlay_label='>Orig', icon=script_icon, command=move_to_origin)
    sm.add_shelf_button(label='Move To Last', overlay_label='>Last', icon=script_icon, command=move_to_last)
    sm.add_shelf_button(label='Rename Nodes', overlay_label='Rname', icon=script_icon, command=rename_nodes)
    sm.add_shelf_button(label='Pivot Match', overlay_label='PvtM', icon=script_icon, command=pivot_match)


def setup_plug_ins():
    check_fbx_plug_in()


def setup_preferences():
    """
    Sets up Maya preferences
    """
    logging.info('>>> Setting Maya preferences')
    cmds.currentUnit(linear='meter')
    grid_size = MAYA_CONFIG.get(section=PREFERENCES_KEY, option='GRID_SIZE', default=3)
    grid_spacing = MAYA_CONFIG.get(section=PREFERENCES_KEY, option='GRID_SPACING', default=1.0)
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
    copy_tree(src=PRESETS_FOLDER.as_posix(), dst=MAYA_APP_DIR.as_posix())


def setup_hotkeys():
    """
    Set up the Robotools hotkeys
    """
    logging.info('>>> Setting up hotkeys')
    RobotoolsHotkeyManager().init_hotkeys()
    RobotoolsHotkeyManager().save_hotkeys()


def robotools_plug_in_path() -> Path or None:
    """
    Get the path of the robotools plug-in if it is in the plug-ins list
    :return:
    """
    plugins = plug_in_utils.list_plug_ins()

    return Path(cmds.pluginInfo(ROBOTOOLS_PLUG_IN, query=True, path=True)) if ROBOTOOLS_PLUG_IN in plugins else None


def install_requirements():
    """
    Install requirements to the site-packages directory
    @return:
    """

    SITE_PACKAGES.mkdir(exist_ok=True)
    cmd = f'{MAYA_INTERPRETER_PATH} -m pip install -r {MAYA_REQUIREMENTS} -t {SITE_PACKAGES} --upgrade'
    logging.debug(f'Terminal command: {cmd}')
    os.system(cmd)
    installed = [x.strip() for x in open(MAYA_REQUIREMENTS, 'r').readlines()]
    logging.info(f'>>> Packages installed: {", ".join(installed)}')


def uninstall_requirements():
    """
    Uninstall requirements and delete site-packages directory
    """
    if SITE_PACKAGES.exists():
        cmd = f'{MAYA_INTERPRETER_PATH} -m pip uninstall -r {MAYA_REQUIREMENTS}'
        os.system(cmd)
        shutil.rmtree(SITE_PACKAGES)


def check_requirements_hash() -> bool:
    """
    Compares the current requirements with the previously used file by comparing hash values
    :return:
    """
    modules_key = 'MODULES'
    requirements_key = 'REQUIREMENTS'
    sha256 = hashlib.sha256()

    with open(MAYA_REQUIREMENTS.as_posix(), 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)

    new_hash = sha256.hexdigest()
    saved_hash = MAYA_CONFIG.get(section=modules_key, option=requirements_key)
    MAYA_CONFIG.set(section=modules_key, option=requirements_key, value=new_hash, save=True)

    return new_hash == saved_hash


def delete_robotools():
    """
    Get rid of the shelf
    """
    logging.info('>>> Deleting Robotools shelf')
    ShelfManager('Robotools').delete()


class RobotoolsHotkeyManager(hotkey_manager.HotkeyManager):
    def __init__(self):
        super(RobotoolsHotkeyManager, self).__init__(name=ROBOTOOLS_HOTKEYS_NAME, path=ROBOTOOLS_HOTKEYS_PATH)

    def init_hotkeys(self):
        """
        Set up the hotkeys
        """
        logging.info('>>> Setting up Robotools hotkeys')
        is_mac: bool = is_using_mac_osx()
        is_pc: bool = not is_using_mac_osx()

        self.set_hotkey('hotkeyPrefs', annotation='Hotkey Editor', mel_command='HotkeyPreferencesWindow',
                        key='H', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('appendToPoly', annotation='Append To Poly', mel_command='AppendToPolygonTool',
                        key='A', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('createPoly', annotation='Create Polygon Tool', mel_command='CreatePolygonTool',
                        key='C', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('combine', annotation='Combine', mel_command='CombinePolygons',
                        key='A', cmd=is_mac, ctrl=is_pc, alt=True, overwrite=True)
        self.set_hotkey('mergeVertices', annotation='Merge Vertices', mel_command='PolyMergeVertices',
                        key='W', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('toggleGrid', annotation='Toggle Grid', mel_command='ToggleGrid',
                        key=';', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('selectEdgeLoop', annotation='Select Edge Loop', mel_command='SelectEdgeLoopSp',
                        key=']', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('selectEdgeRing', annotation='Select Edge Ring', mel_command='SelectEdgeRingSp',
                        key='[', cmd=is_mac, ctrl=is_pc, overwrite=True)
        self.set_hotkey('connect', annotation='Connect', mel_command='ConnectComponents', key='C', overwrite=True)

    def save_hotkeys(self):
        """
        Save the hotkeys file locally
        """
        ROBOTOOLS_HOTKEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.export_set()
