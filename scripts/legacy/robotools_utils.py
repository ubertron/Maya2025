# Robotools version 0.3: New version of Robotools for Maya 2025
import logging
import os
import shutil

from distutils.dir_util import copy_tree
from pathlib import Path
from maya import cmds

from core.core_paths import SITE_PACKAGES, MAYA_INTERPRETER_PATH, MAYA_REQUIREMENTS, image_path, PROJECT_ROOT, \
    PRESETS_DIR
from core.config_utils import MayaConfig
from maya_tools import plug_in_utils
from maya_tools.io.fbx_utils import check_fbx_plug_in
from maya_tools.maya_environment_utils import is_using_mac_osx, MAYA_APP_DIR
from maya_tools.tool_utils import launch_script
from startup.robotools_hotkeys import RobotoolsHotkeys
from startup.robotools_shelf import RobotoolsShelf, TOOL_TITLE


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


def setup_robotools_shelf_():
    logging.info('>>> Setting up Robotools shelf')
    sm = ShelfManager(title=ROBOTOOLS_TITLE)
    sm.delete()
    sm.create(select=True)
    sm.delete_buttons()

    maya_cmds = 'from maya import cmds\n'
    version_info = 'Robotools Shelf Version {}: {}'.format(ROBOTOOLS_SHELF_VERSION, robotools_plug_in_path())
    scene_info = 'from maya_tools import scene_utils; scene_utils.get_scene_path()'
    robonobo_icon = image_path('robonobo_32.png')
    script_icon = image_path('script.png')
    export_manager = 'from maya_tools.ams.ams_debug import launch_export_manager\nlaunch_export_manager()'
    root_name_toggle = 'from maya_tools.ams.ams_debug import root_name_toggle\nroot_name_toggle()'

    character_tools = launch_script(module_name='maya_tools.utilities', script_name='character_tools',
                                    class_name='CharacterTools', object_name='Character Tools')
    base_male_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("male")'
    load_base_male = 'from maya_tools.character_utils import load_base_character\nload_base_character("male")'
    base_female_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("female")'
    load_base_female = 'from maya_tools.character_utils import load_base_character\nload_base_character("female")'

    toggle_layer_shading = 'from maya_tools.layer_utils import toggle_current_layer_shading\ntoggle_current_layer_shading()'
    create_cube = 'from maya import cmds; cmds.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1)'
    slice_cmd = 'from maya_tools.mirror_utils import slice_geometry\nslice_geometry()'
    mirror_cmd = 'from maya_tools.mirror_utils import mirror_geometry\nmirror_geometry()'
    quadrangulate = 'from maya import cmds\ncmds.polyQuad()'
    merge_vertices = f'{maya_cmds}from maya_tools.geometry_utils import merge_vertices\nmerge_vertices(cmds.ls(sl=True)[0])'
    select_triangles = 'from maya_tools import geometry_utils; geometry_utils.get_triangular_faces(select=True)'
    select_ngons = 'from maya_tools import geometry_utils; geometry_utils.get_ngons(select=True)'
    super_reset = 'from maya_tools import node_utils; node_utils.super_reset()'
    pivot_base = 'from maya_tools import node_utils; node_utils.pivot_to_base()'
    pivot_center = 'from maya_tools import node_utils; node_utils.pivot_to_center()'
    pivot_origin = 'from maya_tools import node_utils; node_utils.pivot_to_origin()'
    rebuild_curve = 'from maya_tools import curve_utils; curve_utils.rebuild_closed_curve_from_selected_cv(False)'
    move_to_origin = 'from maya_tools import node_utils; node_utils.move_to_origin()'
    move_to_last = 'from maya_tools import node_utils; node_utils.move_to_last()'
    rename_nodes = 'from maya_tools import node_utils; node_utils.rename_nodes()'
    pivot_match = 'from maya_tools import node_utils; node_utils.match_pivot_to_last()'
    dimensions = 'from maya_tools import helpers; helpers.get_dimensions(format_results=True, clipboard=True)'
    backface_culling = 'from maya_tools.geometry_utils import toggle_backface_culling\ntoggle_backface_culling()'
    toggle_transform_constraints = 'from maya_tools import display_utils\ndisplay_utils.toggle_transform_constraints()'
    toggle_xray = 'from maya_tools.geometry_utils import toggle_xray\ntoggle_xray()'
    combine = f'{maya_cmds}from maya_tools.geometry_utils import combine\ncombine(cmds.ls(sl=True))'
    detach_faces = f'from maya_tools.component_utils import detach_selected_faces\ndetach_selected_faces()'

    sm.add_label('Robotools v{}'.format(ROBOTOOLS_VERSION), bold=True)
    sm.add_shelf_button(label='About Robotools', icon=robonobo_icon, command=message_script(version_info))
    sm.add_shelf_button(label='Scene Info', icon=script_icon, command=scene_info, overlay_label='Scene')
    sm.add_separator()
    sm.add_label('AMS')
    sm.add_shelf_button(label='Export Manager (Debug)', overlay_label='ExMan', icon=script_icon, command=export_manager)
    sm.add_shelf_button(label='Root Name Toggle (Debug)', overlay_label='RtTog', icon=script_icon, command=root_name_toggle)
    sm.add_separator()
    sm.add_label('Characters')
    sm.add_shelf_button(label='Character Tools', icon=script_icon, command=character_tools, overlay_label='CharT')
    sm.add_shelf_button(label='Import Base Male', icon=image_path('base_male.png'), command=base_male_cmd)
    sm.add_shelf_button(label='Load Base Male', icon=script_icon, command=load_base_male, overlay_label='loadM')
    sm.add_shelf_button(label='Import Base Female', icon=image_path('base_female.png'), command=base_female_cmd)
    sm.add_shelf_button(label='Load Base Female', icon=script_icon, command=load_base_female, overlay_label='loadF')
    sm.add_separator()
    sm.add_label('Display')
    sm.add_shelf_button(label='Toggle Layer Shading', icon=script_icon, overlay_label='TgLSh', command=toggle_layer_shading)
    sm.add_shelf_button(label='Get Dimensions', icon=script_icon, overlay_label='Dim', command=dimensions)
    sm.add_shelf_button(label='Toggle Transform Constraints', icon=script_icon, overlay_label='TrCon', command=toggle_transform_constraints)
    sm.add_separator()
    sm.add_label('Geometry')
    sm.add_shelf_button(label='Create Cube', overlay_label='Cube', icon=script_icon, command=create_cube)
    sm.add_shelf_button(label='Slice', icon=image_path('slice.png'), command=slice_cmd)
    sm.add_shelf_button(label='Mirror', icon=image_path('mirror.png'), command=mirror_cmd)
    sm.add_shelf_button(label='Quadrangulate', overlay_label='Quad', icon=script_icon, command=quadrangulate)
    sm.add_shelf_button(label='Merge Vertices', overlay_label='Merge', icon=script_icon, command=merge_vertices)
    sm.add_shelf_button(label='Select Triangles', overlay_label='Tris', icon=script_icon, command=select_triangles)
    sm.add_shelf_button(label='Select Ngons', overlay_label='Ngons', icon=script_icon, command=select_ngons)
    sm.add_shelf_button(label='Toggle Backface Culling', overlay_label='tBFC', icon=script_icon, command=backface_culling)
    sm.add_shelf_button(label='Combine', overlay_label='Cmbn', icon=script_icon, command=combine)
    sm.add_shelf_button(label='Detach Faces', overlay_label='Dtch', icon=script_icon, command=detach_faces)
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
    sm.add_shelf_button(label='Toggle Xray', overlay_label='tXRay', icon=script_icon, command=toggle_xray)
    sm.add_separator()
    sm.add_label('Shapes')
    sm.add_shelf_button(label='Rebuild Curve From CV', overlay_label='Rbld', icon=script_icon, command=rebuild_curve)


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
