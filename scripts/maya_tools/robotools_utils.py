# Robotools version 0.3: New version of Robotools for Maya 2025
import hashlib
import logging
import os

from pathlib import Path
from maya import cmds

from core.core_paths import SITE_PACKAGES, MAYA_INTERPRETER_PATH, MAYA_REQUIREMENTS, icon_path
from core.config_utils import MayaConfig
from maya_tools import plug_in_utils
from maya_tools.utilities.shelf_manager import ShelfManager, message_script

ROBOTOOLS_TITLE: str = 'Robotools'
ROBOTOOLS_VERSION = '0.3'
ROBOTOOLS_PLUG_IN = 'robotools'
ROBOTOOLS_SHELF_VERSION: str = 1.3


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

    logging.info('>>> Setting up Robotools shelf')
    sm = ShelfManager(ROBOTOOLS_TITLE)
    sm.delete()
    sm.create(select=True)
    sm.delete_buttons()

    version_info = 'Robotools Shelf Version {}: {}'.format(ROBOTOOLS_SHELF_VERSION, robotools_plug_in_path())
    robonobo_icon = icon_path('robonobo_32.png')
    script_icon = icon_path('script.png')
    base_male_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("male")'
    load_base_male = 'from maya_tools.character_utils import load_base_character\nload_base_character("male")'
    base_female_cmd = 'from maya_tools.character_utils import import_base_character\nimport_base_character("female")'
    load_base_female = 'from maya_tools.character_utils import load_base_character\nload_base_character("female")'
    create_cube = 'import pymel.core as pm; pm.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1)'
    slice_cmd = 'from maya_tools.mirror_utils import slice_geometry\nslice_geometry()'
    mirror_cmd = 'from maya_tools.mirror_utils import mirror_geometry\nmirror_geometry()'
    quadrangulate = 'import pymel.core as pm\npm.runtime.Quadrangulate()'
    merge_vertices = 'from maya_tools.geometry_utils import merge_vertices\nmerge_vertices'
    select_triangles = 'from maya_tools import geometry_utils; geometry_utils.get_triangular_faces(select=True)'
    select_ngons = 'from maya_tools import geometry_utils; geometry_utils.get_ngons(select=True)'
    super_reset = 'from maya_tools import node_utils; node_utils.super_reset()'
    pivot_base = 'from maya_tools import node_utils; node_utils.pivot_to_base()'
    pivot_center = 'from maya_tools import node_utils; node_utils.pivot_to_center()'
    pivot_origin = 'from maya_tools import node_utils; node_utils.pivot_to_origin()'
    move_to_origin = 'from maya_tools import node_utils; node_utils.move_to_origin()'

    sm.add_label('Robotools v{}'.format(ROBOTOOLS_VERSION), bold=True)
    sm.add_shelf_button(label='About Robotools', icon=robonobo_icon, command=message_script(version_info))
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
    sm.add_separator()
    sm.add_label('Nodes')
    sm.add_shelf_button(label='Super Reset', overlay_label='SpRst', icon=script_icon, command=super_reset)
    sm.add_shelf_button(label='Pivot To Base', overlay_label='Pv->B', icon=script_icon, command=pivot_base)
    sm.add_shelf_button(label='Pivot To Center', overlay_label='Pv->C', icon=script_icon, command=pivot_center)
    sm.add_shelf_button(label='Pivot To Origin', overlay_label='Pv->O', icon=script_icon, command=pivot_origin)
    sm.add_shelf_button(label='Move To Origin', overlay_label='>Orig', icon=script_icon, command=move_to_origin)

    # logging.info('>>> Setting up Robotools hotkeys')


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
    config = MayaConfig()
    saved_hash = config.get(section=modules_key, option=requirements_key)
    config.set(section=modules_key, option=requirements_key, value=new_hash, save=True)

    return new_hash == saved_hash


def delete_robotools():
    """
    Get rid of the shelf
    """
    logging.info('>>> Deleting Robotools shelf')
    # ShelfManager('Robotools').delete()
