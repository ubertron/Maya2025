from maya import cmds
from typing import List


def get_vertex_count(transform) -> int:
    """
    Get the number of vertices in a transform
    :param transform:
    :return:
    """
    return cmds.polyEvaluate(transform, vertex=True)


def get_vertex_positions(transform: str) -> List[List[float]]:
    """
    Gets the position of each vertex in a mesh
    :param transform:
    :return:
    """
    vertex_list = range(get_vertex_count(transform))
    return [cmds.pointPosition(f'{transform}.vtx[{i}]', world=True) for i in vertex_list]
