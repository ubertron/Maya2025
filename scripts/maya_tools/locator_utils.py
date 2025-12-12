from maya import cmds

from core.point_classes import Point3
from maya_tools import node_utils, geometry_utils
from maya_tools.undo_utils import UndoStack


DEFAULT_SIZE: float = 10.0


def create_locator(position: Point3, name: str = "locator", size: float=DEFAULT_SIZE) -> str:
    """Create a locator."""
    result = cmds.spaceLocator()
    locator = result[0]
    new_name = cmds.rename(locator, name)
    cmds.setAttr(f"{new_name}.localScale", size, size, size, type="float3")
    cmds.setAttr(f"{new_name}.translate", *position.values, type="float3")
    return new_name


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


def zero_locator_rotations():
    selected = cmds.ls(sl=True)
    if len(selected) == 1 and selected[0] in node_utils.get_locators():
        with UndoStack("Zero Rotations"):
            zero_rotations(selected[0])
            cmds.select(selected)
    else:
        print(f"Please select a single locator")


def zero_rotations(node: str):
    children = cmds.listRelatives(node, children=True, type='transform')
    if children:
        cmds.parent(children, world=True)
        cmds.setAttr(f"{node}.rotate", 0, 0, 0, type="float3")
        cmds.parent(children, node)
        for child in children:
            zero_rotations(child)
    else:
        cmds.setAttr(f"{node}.rotate", 0, 0, 0, type="float3")
