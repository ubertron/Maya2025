from maya import cmds

from maya_tools import node_utils
from maya_tools.undo_utils import UndoStack


def zero_locator_rotations():
    selected = cmds.ls(sl=True)
    if len(selected) == 1 and selected[0] in node_utils.get_locators():
        with UndoStack("Zero Rotations"):
            zero_rotations(selected[0])
            cmds.select(selected)
    else:
        print(f"Please select a single locator")


def zero_rotations(transform: str):
    children = cmds.listRelatives(transform, children=True, type='transform')
    if children:
        cmds.parent(children, world=True)
        cmds.setAttr(f"{transform}.rotate", 0, 0, 0, type="float3")
        cmds.parent(children, transform)
        for child in children:
            zero_rotations(child)
    else:
        cmds.setAttr(f"{transform}.rotate", 0, 0, 0, type="float3")
