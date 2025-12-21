from maya import cmds
from typing import Optional, Union

from core.core_enums import Axis
from core.point_classes import Point3, ZERO3
from maya_tools.node_utils import get_root_transform


def mirror_geometry(nodes: Optional[Union[str, list]] = None, axis: Axis = Axis.x, positive: bool = False,
                    merge_threshold: float = 0.001, pivot: Optional[Point3] = None) -> list[str]:
    """
    Mirrors geometry along an axis
    :param nodes: Supply nodes
    :param axis: Specify geometric axis
    :param positive: Specify positive or negative axis
    :param merge_threshold: threshold along axis
    :param pivot:
    """
    selection = cmds.ls(sl=True)
    nodes = cmds.ls(nodes) if nodes else cmds.ls(sl=True, tr=True)
    direction = {
        Axis.x: 0 + positive,
        Axis.y: 2 + positive,
        Axis.z: 4 + positive
    }

    for item in nodes:
        cmds.select(item)

        if pivot:
            pivot_position = pivot.values
        else:
            root_node = get_root_transform(item)
            pivot_position = [cmds.xform(root_node, query=True, piv=True, ws=True)[i] for i in range(3)]

        slice_geometry(item, axis, not positive)
        cmds.polyMirrorFace(item,  ws=True, d=direction[axis], mergeMode=1, p=pivot_position, mt=merge_threshold, mtt=1)

    cmds.select(selection)

    return nodes


def slice_geometry(nodes=None, axis=Axis.x, positive=True, pivot: Optional[Point3] = None) -> list[str]:
    """
    Slices geometry along an axis
    :param nodes:
    :param axis: Specify geometric axis
    :param positive: Specify positive or negative axis
    """
    selection = cmds.ls(sl=True)
    nodes = cmds.ls(nodes) if nodes else cmds.ls(sl=True, tr=True)
    angles = {
        Axis.x: [0, positive * 180 - 90, 0],
        Axis.y: [90 - positive * 180, 0, 0],
        Axis.z: [0, 180 - positive * 180, 0]
    }
    cut_axis = angles[axis]

    for item in nodes:
        cmds.select(item)

        if pivot:
            pivot_position = pivot.values
        else:
            root_node = get_root_transform(item)
            pivot_matrix = cmds.xform(root_node, query=True, piv=True, ws=True)
            pivot_position = [pivot_matrix[0], pivot_matrix[1], pivot_matrix[2]]

        cmds.polyCut(
            cutPlaneCenter=pivot_position,
            cutPlaneRotate=cut_axis,
            extractFaces=True,
            extractOffset=[0, 0, 0],
            deleteFaces=True
        )

    cmds.select(selection)

    return nodes


def flip_geometry(nodes: Optional[Union[str, list]] = None, axis: Axis = Axis.x, positive: bool = True,
                  pivot: Optional[Point3] = None):
    """
    Combine mirror and slice to flip geometry
    N.B. Only works from one side to another so geometry needs to be distinct on one positive or negative axial side
    Alternative to negative scaling
    :param nodes:
    :param axis:
    :param positive:
    :param pivot:
    """
    nodes = cmds.ls(nodes) if nodes else cmds.ls(sl=True, tr=True)
    mirror_geometry(nodes=nodes, axis=axis, positive=positive, pivot=pivot)
    slice_geometry(nodes=nodes, axis=axis, positive=not positive, pivot=pivot)
