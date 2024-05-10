import math

from maya import cmds
from typing import List, Optional

from maya_tools.scene_utils import message_script
from maya_tools.node_utils import State


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


def create_cube(name: Optional[str] = None, size: int = 1, divisions: int = 1) -> str:
    """
    Mirrors geometry along an axis
    :param name: str
    :param size: int
    :param divisions: int
    """
    cube, _ = cmds.polyCube(
        name=name if name else 'cube',
        width=size, height=size, depth=size,
        sx=divisions,  sy=divisions, sz=divisions)

    return cube


def merge_vertices(transform=None, precision=5) -> str:
    """
    Merge vertices
    @param transform:
    @param precision:
    @return:
    """
    state = State()
    transform = cmds.ls(transform, tr=True) if transform else cmds.ls(sl=True, tr=True)
    result = cmds.polyMergeVertex(transform, distance=precision_to_threshold(precision))
    state.restore()

    return cmds.ls(result[0])[0]


def precision_to_threshold(precision=1):
    """
    Convert digits of precision to a float threshold
    @param precision:
    @return:
    """
    return 1.0 / math.pow(10, precision)


def get_triangular_faces(transform=None, select=False):
    """
    Get a list of triangular faces
    @param transform:
    @param select:
    """
    get_faces_by_vert_count(transform=transform, select=select, face_type='triangle')


def get_quads(transform=None, select=False):
    """
    Get a list of triangular faces
    @param transform:
    @param select:
    """
    get_faces_by_vert_count(transform=transform, select=select, face_type='quad')


def get_ngons(transform=None, select=False):
    """
    Get a list of ngons
    @param transform:
    @param select:
    """
    get_faces_by_vert_count(transform=transform, select=select, face_type='ngon')


def get_faces_by_vert_count(transform: Optional[str] = None, select: bool = False, face_type: str = 'quad'):
    """
    Get a list of the face ids for faces by face type
    :param transform:
    :param select:
    :param face_type: 'ngon' | 'quad' | 'triangle'
    :return:
    """
    transform = cmds.ls(transform, tr=True) if transform else cmds.ls(sl=True, tr=True)

    if len(transform) != 1:
        cmds.warning('Please supply a single transform')
        return False
    else:
        transform = transform[0]

    num_faces = cmds.polyEvaluate(transform, face=True)
    vertex_dict = {'triangle': [], 'quad': [], 'ngon': []}

    for i in range(num_faces):
        vertices = cmds.polyListComponentConversion(f'{transform}.f[{i}]', tv=True)
        vertex_count = len(cmds.ls(vertices, flatten=True))
        if vertex_count == 3:
            key = 'triangle'
        elif vertex_count == 4:
            key = 'quad'
        else:
            key = 'ngon'
        vertex_dict[key].append(i)

    result = vertex_dict[face_type]

    if select and len(result):
        select_faces(transform=transform, vertices=result)
    else:
        return vertex_dict[return_type]


def select_faces(transform: str, vertices: List[int]):
    """
    Select faces on a mesh
    :param transform:
    :param vertices:
    """
    face_objects = [f'{transform}.f[{x}]' for x in vertices]
    cmds.select(face_objects)
    cmds.hilite(transform)
    cmds.selectType(facet=True)
