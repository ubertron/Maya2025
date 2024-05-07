# Robotools version 0.3: New version of Robotools for Maya 2025
import logging

from pathlib import Path
from maya import cmds

from core.core_paths import icon_path
# from maya_utils.utilities.shelf_manager import ShelfManager, message_script

ROBOTOOLS_TITLE: str = 'Robotools'
ROBOTOOLS_VERSION = '0.3'
ROBOTOOLS_PLUG_IN = 'robotools'
# ROBOTOOLS_PLUG_IN_PATH = Path(cmds.pluginInfo(ROBOTOOLS_PLUG_IN, query=True, path=True))


def setup_robotools():
    """
    Sets up Robotools
    """
    logging.info('>>> Setting up Robotools shelf')
    # sm = ShelfManager(ROBOTOOLS_TITLE)
    # sm.delete()
    # sm.create(select=True)
    # sm.delete_buttons()
    #
    # version_info = f'Robotools Version {ROBOTOOLS_VERSION}: {ROBOTOOLS_PLUG_IN_PATH.as_posix()}'
    # robonobo_icon = icon_path('robonobo_32.png')
    # script_icon = icon_path('script.png')
    # import_base_male = 'from maya_utils.character_utils import import_base_character\nimport_base_character("male")'
    # load_base_male = 'from maya_utils.character_utils import load_base_character\nload_base_character("male")'
    # import_base_female = 'from maya_utils.character_utils import import_base_character\nimport_base_character("female")'
    # load_base_female = 'from maya_utils.character_utils import load_base_character\nload_base_character("female")'
    # slice_geometry = 'from maya_utils.geometry_utils import slice_geometry\nslice_geometry()'
    # mirror = 'from maya_utils.geometry_utils import mirror_geometry\nmirror_geometry()'
    # merge = 'from maya_utils.geometry_utils import merge_vertices\nmerge_vertices()'
    # quadrangulate = 'from maya_utils.geometry_utils import quadrangulate\nquadrangulate()'
    #
    # sm.add_shelf_button(label=ROBOTOOLS_TITLE, icon=robonobo_icon, command=message_script(version_info))
    # sm.add_separator()
    # sm.add_shelf_button(label='Import Base Male', icon=icon_path('base_male.png'), command=import_base_male)
    # sm.add_shelf_button(label='Load Base Male', icon=script_icon, command=load_base_male, overlay_label='loadM')
    # sm.add_shelf_button(label='Import Base Female', icon=icon_path('base_female.png'), command=import_base_female)
    # sm.add_shelf_button(label='Load Base Female', icon=script_icon, command=load_base_female, overlay_label='loadF')
    # sm.add_separator()
    # sm.add_shelf_button(label='Slice', icon=icon_path('slice.png'), command=slice_geometry)
    # sm.add_shelf_button(label='Mirror', icon=icon_path('mirror.png'), command=mirror)
    # sm.add_shelf_button(label='Merge Vertices', icon=script_icon, overlay_label='merge', command=merge)
    # sm.add_shelf_button(label='Quadrangulate', icon=script_icon, overlay_label='quad', command=quadrangulate)


def delete_robotools():
    """
    Get rid of the shelf
    """
    logging.info('>>> Deleting Robotools shelf')
    # ShelfManager('Robotools').delete()
