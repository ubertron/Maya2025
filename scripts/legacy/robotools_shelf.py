"""Shelf for Robotools."""
import logging
from functools import partial
from maya import cmds, mel

import maya_tools.node_utils
from core.version_info import VersionInfo
from core.core_paths import image_path
from core import logging_utils
from legacy.shelf_manager import ShelfManager
from maya_tools import display_utils, geometry_utils, mirror_utils, node_utils, layer_utils, scene_utils

TOOL_TITLE = 'Robotools'
VERSIONS = (
    VersionInfo(name=TOOL_TITLE, version="1.0", codename="Dr No", info="Initial release"),
    VersionInfo(name=TOOL_TITLE, version="2.0", codename="Thunderball", info="Update to new ShelfManager"),
)
SCRIPT_ICON = image_path("custom_script.png")
LOGGER = logging_utils.get_logger(name=__name__, level=logging.INFO)


class RobotoolsShelf(ShelfManager):
    """Shelf for Robotools."""

    def __init__(self):
        super().__init__(title=TOOL_TITLE)

    def initialize_buttons(self) -> None:
        """Initialize buttons."""
        self.add_button(label='About Robotools', icon=image_path('robonobo_32.png'),
                        command=lambda: display_utils.info_message(VERSIONS[-1].title))
        self.add_button(label='Scene Info', icon=SCRIPT_ICON,
                        command=self.scene_info, overlay_label='Scene')
        self.add_separator()
        self.add_panel_button(label='Characters', overlay_label='Chars',
                              linked_labels=["Character Tools", 'Import Base Male', 'Load Base Male',
                                             'Import Base Female', 'Load Base Female'])
        self.add_button(label='Character Tools', icon=SCRIPT_ICON, command=self.character_tools, overlay_label='ChrT')
        self.add_button(label='Load Base Male', icon=image_path('load_male.png'),
                        command=partial(self.load_base_character, name='male'))
        self.add_button(label='Import Base Male', icon=image_path('import_male.png'),
                        command=partial(self.import_base_character, name="male"))
        self.add_button(label='Load Base Female', icon=image_path('load_female.png'),
                        command=partial(self.load_base_character, name='female'))
        self.add_button(label='Import Base Female', icon=image_path('import_female.png'),
                        command=partial(self.import_base_character, name="female"))
        self.add_separator()
        self.add_panel_button(label='Display', overlay_label='Dsply',
                              linked_labels=["Toggle Layer Shading", 'Get Dimensions', "Toggle Xray",
                                             'Toggle Transform Constraints'], state=True)
        self.add_button(label='Toggle Layer Shading', icon=SCRIPT_ICON, overlay_label='TgLSh',
                        command=layer_utils.toggle_current_layer_shading)
        self.add_button(label='Get Dimensions', icon=SCRIPT_ICON, overlay_label='Dim', command=self.get_dimensions)
        self.add_button(label='Toggle Transform Constraints', icon=SCRIPT_ICON, overlay_label='TrCon',
                        command=display_utils.toggle_transform_constraints)
        self.add_button(label='Toggle Xray', icon=SCRIPT_ICON, overlay_label="Xray", command=geometry_utils.toggle_xray)
        self.add_separator()
        self.add_panel_button(label='Geometry', overlay_label='Geo', linked_labels=["Create Cube", 'Slice', 'Mirror', 'Quadrangulate', 'Merge Vertices'], state=True)
        self.add_button(label='Create Cube', icon=image_path("cube.png"), command=lambda: mel.eval("polyCube;"))
        self.add_button(label='Slice', icon=image_path('slice.png'), command=mirror_utils.slice_geometry)
        self.add_button(label='Mirror', icon=image_path('mirror.png'), command=mirror_utils.mirror_geometry)
        self.add_button(label='Quadrangulate', overlay_label='Quad', icon=SCRIPT_ICON, command=lambda: exec('from maya import cmds\ncmds.polyQuad()'))
        self.add_button(label='Merge Vertices', overlay_label='Merge', icon=SCRIPT_ICON, command=self.merge_vertices)
        # self.add_button(label='Select Triangles', overlay_label='Tris', icon=SCRIPT_ICON, command=select_triangles)
        # self.add_button(label='Select Ngons', overlay_label='Ngons', icon=SCRIPT_ICON, command=select_ngons)
        # self.add_button(label='Toggle Backface Culling', overlay_label='tBFC', icon=SCRIPT_ICON, command=backface_culling)
        # self.add_button(label='Combine', overlay_label='Cmbn', icon=SCRIPT_ICON, command=combine)
        # self.add_button(label='Detach Faces', overlay_label='Dtch', icon=SCRIPT_ICON, command=detach_faces)
        self.add_separator()
        self.add_panel_button(label="Nodes", overlay_label="Nodes",
                              linked_labels=["Super Reset", "Pivot To Base", "Pivot To Center", "Pivot To Origin",
                                             "Move To Origin", "Move To Last", "Rename Nodes", "Pivot Match"],
                              state=True)
        self.add_button(label='Super Reset', icon=image_path("super_reset.png"), command=node_utils.super_reset)
        self.add_button(label='Pivot To Base', icon=SCRIPT_ICON, overlay_label="Pv > B",
                        command=node_utils.pivot_to_base)
        self.add_button(label='Pivot To Center', icon=SCRIPT_ICON, overlay_label="Pv > C",
                        command=node_utils.pivot_to_center)
        self.add_button(label='Pivot To Origin', icon=SCRIPT_ICON, overlay_label="Pv > O",
                        command=node_utils.pivot_to_origin)
        self.add_button(label='Move To Origin', icon=SCRIPT_ICON, overlay_label="M > O",
                        command=node_utils.move_to_origin)
        self.add_button(label='Move To Last', icon=SCRIPT_ICON, overlay_label="M > L", command=node_utils.move_to_last)
        self.add_button(label='Pivot Match', icon=SCRIPT_ICON, overlay_label="Pv M",
                        command=node_utils.match_pivot_to_last)
        self.add_separator()
        self.add_panel_button(label="Utilities", overlay_label="Utils",
                              linked_labels=["File Path Editor", "Path Tool", "Combine"], state=True)
        self.add_button(label="File Path Editor", icon=image_path("file_path_editor.png"),
                        command=lambda: mel.eval("filePathEditorWin;"))
        self.add_button(label='Combine', overlay_label='Cmbn', icon=SCRIPT_ICON, command=self.combine)
        self.add_button(label='Path Tool', icon=image_path("path_tool.png"), command=self.path_tool)
        self.add_separator()

    @staticmethod
    def import_base_character(name: str) -> None:
        from maya_tools.character_utils import import_base_character
        import_base_character(name)

    @staticmethod
    def load_base_character(name: str) -> None:
        from maya_tools.character_utils import load_base_character
        load_base_character(name)

    @staticmethod
    def character_tools():
        """Launch character tools."""
        from maya_tools.utilities import character_tools
        ui_script = "from maya_tools.utilities import character_tools; character_tools.CharacterTools().restore()"
        character_tools.CharacterTools().show_workspace_control(ui_script=ui_script)

    @staticmethod
    def combine():
        from maya_tools import geometry_utils, node_utils
        geometry_utils.combine(node_utils.get_selected_transforms())

    @staticmethod
    def get_dimensions():
        from maya_tools import helpers
        maya_tools.node_utils.get_dimensions(format_results=True, clipboard=True)

    @staticmethod
    def merge_vertices() -> None:
        nmerge_vertices(cmds.ls(sl=True)[0])

    @staticmethod
    def scene_info():
        scene_path = scene_utils.get_scene_path()
        display_utils.info_message(scene_path if scene_path else "No scene loaded.")

    @staticmethod
    def path_tool():
        """Launch Path Tool."""
        from utilities.path_tool import path_tool
        ui_script = "from utilities.path_tool import path_tool; path_tool.PathTool().restore()"
        path_tool.PathTool().show_workspace_control(ui_script=ui_script)
