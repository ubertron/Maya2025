"""
Scripts for developing the AMS tools
"""
from importlib import reload
from core import core_enums; reload(core_enums)
from maya import cmds

from maya_tools.ams import ams_enums; reload(ams_enums)
from widgets import panel_widget; reload(panel_widget)
from maya_tools.ams import asset; reload(asset)
from maya_tools.ams import asset_metadata; reload(asset_metadata)
from maya_tools import layer_utils; reload(layer_utils)
from maya_tools.io import fbx_preset; reload(fbx_preset)
from maya_tools import maya_enums; reload(maya_enums)
from maya_tools.ams import export_utils; reload(export_utils)
from maya_tools.ams import asset; reload(asset)
from maya_tools.ams import project_utils; reload(project_utils)
from maya_tools.ams import character_exporter; reload(character_exporter)
from maya_tools.ams import export_manager; reload(export_manager)
from maya_tools.display_utils import in_view_message


def launch_export_manager():
    """
    Launch debug version of Export Manager
    """
    if 'em' in globals():
        em.close()

    em = export_manager.ExportManager()
    # em.show()
    em.show_workspace_control()


def root_name_toggle():
    """
    Script toggles the name of the character skeleton root node
    """
    original_root = '|Group|DeformationSystem|Root_M'
    altered_root = '|Group|DeformationSystem|Root_M_altered'

    if cmds.objExists(original_root):
        in_view_message("Renaming Root_M to Root_M_altered")
        cmds.rename(original_root, altered_root.split('|')[-1])
    elif cmds.objExists(altered_root):
        in_view_message("Renaming Root_M_altered to Root_M")
        cmds.rename(altered_root, original_root.split('|')[-1])
    else:
        in_view_message("Neither root object found. Please reload scene")