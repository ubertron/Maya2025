import math

from maya import cmds
import maya.api.OpenMaya as om
from typing import Optional, Sequence, Union

from core.core_enums import ComponentType
from core.point_classes import Point3
from maya_tools.scene_utils import message_script
from maya_tools.node_utils import State, set_component_mode, get_component_mode, get_type_from_transform


def get_transforms(node: str = '', single: bool = True) -> str or list[str] or None:
    """
    Gets the currently selected transform whether in object mode or component mode
    :param node:
    :param single:
    :return:
    """
    state = State()
    set_component_mode(component_type=ComponentType.object)
    node_list = cmds.ls(node) if node else cmds.ls(sl=True, tr=True)
    state.restore()

    if single:
        return node_list[0] if len(node_list) == 1 else None
    else:
        return node_list


def get_selected_edges(node: str = '') -> list[int] or None:
    """
    Gets a list of the edge ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.edge)


def get_selected_vertices(node: str = '') -> list[int] or None:
    """
    Gets a list of the vertex ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.vertex)


def get_selected_faces(node: str = '') -> list[int] or None:
    """
    Gets a list of the face ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.face)


def get_selected_components(node: str = '', component_type: ComponentType = ComponentType.face) -> list[int] or None:
    """
    Gets a list of the component ids, or None if node not found
    :param node:
    :param component_type:
    :return:
    """
    node = get_transforms(node)
    assert component_type in (ComponentType.face, ComponentType.vertex, ComponentType.edge), 'Component not supported.'
    assert node, 'Please supply a node.'
    component_label: dict = {ComponentType.edge: 'e', ComponentType.face: 'f', ComponentType.vertex: 'vtx'}
    state = State()
    cmds.select(node)
    set_component_mode(component_type=component_type)
    selection = cmds.ls(sl=True, flatten=True)
    state.restore()
    component_prefix = f'{node}.{component_label[component_type]}['
    component_ids = [int(x.split(component_prefix)[1].split(']')[0]) for x in selection]

    return component_ids


def get_vertex_count(transform) -> int:
    """
    Get the number of vertices in a transform
    :param transform:
    :return:
    """
    return cmds.polyEvaluate(transform, vertex=True)


def get_vertex_positions(transform: str) -> list[Point3]:
    """
    Gets the position of each vertex in a mesh
    :param transform:
    :return:
    """
    vertex_list = range(get_vertex_count(transform))

    return [get_vertex_position(transform=transform, vertex_id=i) for i in vertex_list]


def get_vertex_position(transform: str, vertex_id: int) -> Point3:
    """
    Get the position of a vertex or cv on a transform
    :param transform:
    :param vertex_id:
    :return:
    """
    component_prefix = {'nurbsSurface': 'cv', 'mesh': 'vtx'}[get_type_from_transform(transform)]

    return Point3(*cmds.pointPosition(f'{transform}.{component_prefix}[{vertex_id}]', world=True))


def get_vertex_face_list(transform: str):
    """
    Get a list of vertices by face
    :param transform:
    :return:
    """
    selection_list = om.MSelectionList()
    selection_list.add(transform)
    dagPath = selection_list.getDagPath(0)
    fnMesh = om.MFnMesh(dagPath)

    cursor, out = 0, []
    counts, indices = fnMesh.getVertices()

    # `counts` contains the number of vertexes per face
    # `indices` is a list of all indices for all faces

    # So if counts was [4, 3, 5], the first 4 indices in idxs
    # would be the verts for the first face. The next 3 indices
    # in indices would be the verts for the second face. The next 5
    # would belong to the third face.

    for i, count in enumerate(counts):
        # Cast to list as an om.MIntArray is the result
        out.append(list(indices[cursor: cursor + count]))
        cursor += count

    return out


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


def select_faces(transform: str, vertices: list[int]):
    """
    Select faces on a mesh
    :param transform:
    :param vertices:
    """
    face_objects = [f'{transform}.f[{x}]' for x in vertices]
    cmds.select(face_objects)
    cmds.hilite(transform)
    cmds.selectType(facet=True)


def set_edge_softness(node_selection: Union[str, list[str]], angle: float = 30):
    """
    Set
    :param node_selection:
    :param angle:
    """
    state = State()
    cmds.select(node_selection)
    cmds.polySoftEdge(angle=angle)
    state.restore()


def get_component_indices(component_list: list[str], component_type: ComponentType = ComponentType.edge):
    """
    Converts a component list to indices
    :param component_list:
    :type component_type:
    :return:
    """
    component = {
        ComponentType.edge: 'e',
        ComponentType.vertex: 'vtx',
        ComponentType.face: 'f'
    }

    flat_list = cmds.ls(component_list, flatten=True)
    return [x.split(f'.{component[component_type]}[')[1].split(']')[0] for x in flat_list]


def get_open_edges(transform: str, select=False):
    """
    Gets the open edges on a mesh
    :param transform:
    :param select:
    :return:
    """
    cmds.select(transform)
    cmds.polySelectConstraint(mode=3, type=0x8000, where=1)
    border_edges = cmds.ls(sl=True)
    cmds.polySelectConstraint(mode=0)

    if select:
        cmds.select(border_edges)

    return get_component_indices(component_list=border_edges, component_type=ComponentType.edge)


def toggle_backface_culling(transforms: Optional[Sequence[str]] = None):
    """
    Toggle backface culling on passed or selected objects
    :param transforms:
    """
    transforms = list(cmds.ls(transforms)) if transforms else cmds.ls(sl=True, transforms=True)

    for item in transforms:
        value = f'{item}.backfaceCulling'
        cmds.setAttr(value, 3) if cmds.getAttr(value) == 0 else cmds.setAttr(value, 0)


def toggle_xray(transforms: Optional[Sequence[str]] = None):
    """
    Toggle xray on passed or selected objects
    :param transforms:
    """
    transforms = list(cmds.ls(transforms)) if transforms else cmds.ls(sl=True, transforms=True)

    for item in transforms:
        cmds.displaySurface(item, xRay=(not cmds.displaySurface(item, xRay=True, query=True)[0]))


def create_hemispheroid(name: str = 'hemispheroid', diameter: float = 1.0, height: float = 0.5, primitive: int = 2,
                        subdivisions: int = 3, base: bool = True, select: bool = True,
                        construction_history: bool = True):
    """
    Create a polygon hemispheroid
    :param name:
    :param diameter:
    :param height:
    :param primitive:
    :param subdivisions:
    :param base:
    :param select:
    :param construction_history:
    :return:
    """
    hemispheroid = cmds.polyPlatonic(radius=diameter / 2, primitive=primitive, subdivisionMode=0,
                                     subdivisions=subdivisions, sphericalInflation=1)[0]
    cmds.delete(hemispheroid, ch=True)
    hemispheroid = cmds.rename(hemispheroid, name)
    cmds.setAttr(f'{hemispheroid}.scaleY', height * 2.0 / diameter)
    cmds.makeIdentity(hemispheroid, apply=True, scale=True)

    # delete faces below y = 0
    verts_below_0 = [i for i, value in enumerate(get_vertex_positions(transform=hemispheroid)) if value.y < 0]
    vert_list_by_face = get_vertex_face_list(transform=hemispheroid)
    faces_below_0 = [i for i, verts in enumerate(vert_list_by_face) for v in verts if v in verts_below_0]
    select_faces(hemispheroid, faces_below_0)
    cmds.delete(cmds.ls(sl=True))

    # create base
    if base:
        get_open_edges(hemispheroid, select=True)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), localTranslateZ=-0.1)
        cmds.move(0, cmds.ls(sl=True), moveY=True, absolute=True)
        verts = cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True)
        cmds.polyMergeVertex(verts, distance=precision_to_threshold(diameter))

    if not construction_history:
        cmds.delete(hemispheroid, ch=True)

    set_component_mode(ComponentType.object)

    if select:
        cmds.select(hemispheroid)
    else:
        cmds.select(clear=True)

    return hemispheroid
