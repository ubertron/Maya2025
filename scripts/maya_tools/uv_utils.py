"""UV Utils."""
from __future__ import annotations

from maya import cmds

from maya_tools.node_utils import State


def box_map(transform: str | None = None, size: float = 100.0):
    """UV-texting to a fixed world scale.
    https://help.autodesk.com/cloudhelp/ENU/MayaCRE-Tech-Docs/CommandsPython/polyAutoProjection.html
    """
    state = State()
    selection = cmds.ls(transform) if transform else cmds.ls(selection=True)
    maps = []
    if selection:
        for x in selection:
            result = cmds.polyAutoProjection(
                x,
                layout=0,
                worldSpace=1,
                scaleMode=1,
                planes=6,
                scale=(size, size, size)
            )
            maps.append(result[0])
    state.restore()
    return maps


if __name__ == "__main__":
    box_map()
