"""uv_utils.py

Utilities to handle texturing
"""
from maya import cmds
from maya_tools import node_utils


def box_map(size: float = 100.0):
    """UV-texting to a fixed world scale.
    https://help.autodesk.com/cloudhelp/ENU/MayaCRE-Tech-Docs/CommandsPython/polyAutoProjection.html
    """
    selection = node_utils.get_selected_transforms()
    for x in selection:
        cmds.polyAutoProjection(
            x,
            layout=0,
            worldSpace=1,
            scaleMode=1,
            planes=6,
            scale=(size, size, size)
        )
    cmds.select(selection)


if __name__ == "__main__":
    box_map()
