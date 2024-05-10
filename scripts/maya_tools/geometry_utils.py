from maya import cmds
from typing import List

from maya_tools.scene_utils import message_script


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


def create_cube(name=None, size=1, divisions=1):
    """
    Mirrors geometry along an axis
    :param name: str
    :param size: int
    :param divisions: int
    """
    cube, _ = pm.polyCube(name=name if name else 'cube', width=size, height=size, depth=size, sx=divisions,
                          sy=divisions, sz=divisions)
    return cube


def merge_vertices(transform=None, precision=5):
    """
    Merge vertices
    @param transform:
    @param precision:
    @return:
    """
    transform = pm.ls(transform, tr=True) if transform else pm.ls(sl=True, tr=True)
    result = pm.polyMergeVertex(transform, distance=precision_to_threshold(precision))
    return pm.ls(result[0])[0]


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
    get_non_quad_faces(transform=transform, select=select, triangles=True, quads=False, ngons=False)


def get_quads(transform=None, select=False):
    """
    Get a list of triangular faces
    @param transform:
    @param select:
    """
    get_non_quad_faces(transform=transform, select=select, triangles=False, quads=True, ngons=False)


def get_ngons(transform=None, select=False):
    """
    Get a list of ngons
    @param transform:
    @param select:
    """
    get_non_quad_faces(transform=transform, select=select, triangles=False, quads=False, ngons=True)


def get_faces_by_vert_count(transform=None, select=False, triangles=False, quads=True, ngons=False):
    """
    Get a list of the face ids for faces that do not have 4 vertices
    @param transform:
    @param select:
    @param triangles:
    @param quads:
    @param ngons:
    @return:
    """
    transform = pm.ls(transform, tr=True) if transform else pm.ls(sl=True, tr=True)

    if len(transform) != 1:
        pm.warning('Please supply a single transform')
        return False
    else:
        transform = transform[0]

    mesh = pm.PyNode(transform)
    result = []

    if triangles:
        result.extend(face.index() for face in mesh.faces if len(face.getVertices()) == 3)

    if quads:
        result.extend(face.index() for face in mesh.faces if len(face.getVertices()) == 3)

    if ngons:
        result.extend(face.index() for face in mesh.faces if len(face.getVertices()) > 4)

    logging.info('{} {} found in {}'.format(len(result), 'faces', transform.name()))

    if select and len(result) > 0:
        pm.select(transform.f[result])
        pm.hilite(transform)
        pm.selectType(facet=True)
    else:
        return result