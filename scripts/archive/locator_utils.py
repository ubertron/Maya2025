from maya import cmds

from core.point_classes import Point3
from maya_tools import node_utils, geometry_utils
from maya_tools.undo_utils import UndoStack


DEFAULT_SIZE: float = 10.0


def create_vertex_locators(size: float = DEFAULT_SIZE):
    """Create locators at the position of selected vertices."""
    state = node_utils.State()
    geometry = node_utils.get_selected_geometry()
    for obj in geometry:
        selected_verts = geometry_utils.get_selected_vertices(obj)
        for vert in selected_verts:
            position = geometry_utils.get_vertex_position(node=obj, vertex_id=vert)
            locator = cmds.spaceLocator()
            cmds.setAttr(f"{locator[0]}.localScale", size, size, size, type="float3")
            print(*position.values)
            cmds.setAttr(f"{locator[0]}.translate", *position.values, type="float3")
    state.restore()
