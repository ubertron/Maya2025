"""UV Utils."""
from __future__ import annotations

from maya import cmds


def box_map(transform: str | None = None, size: float = 100.0):
    """UV-texting to a fixed world scale.
    https://help.autodesk.com/cloudhelp/ENU/MayaCRE-Tech-Docs/CommandsPython/polyAutoProjection.html
    """
    selection = transform if transform else cmds.ls(selection=True)
    cmds.polyAutoProjection(
        selection,
        layout=0,
        worldSpace=1,
        scaleMode=1,
        planes=6,
        scale=(size, size, size)
    )


if __name__ == "__main__":
    box_map()
