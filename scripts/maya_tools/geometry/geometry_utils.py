from __future__ import annotations

import logging

import math
import maya.api.OpenMaya as om

from dataclasses import dataclass
from maya import cmds
from typing import Optional, Sequence, Union

from core import logging_utils
from core.color_classes import RGBColor
from core.core_enums import ComponentType, Axis
from core.point_classes import Point3, Point3Pair, NEGATIVE_Y_AXIS, ZERO3
from core.math_utils import dot_product, normalize_vector, degrees_to_radians, get_midpoint_from_point_list
from maya_tools import display_utils, node_utils
from maya_tools.geometry import component_utils
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import set_translation

LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)


def combine(transforms: list[str] | None = None, name: str = '', position: Optional[Point3] = None,
            parent: Optional[str] = None, history: bool = False) -> str or None:
    """Combine geometry nodes."""
    if transforms is None:
        transforms = cmds.ls(selection=True, transforms=True)
    mesh_transforms = [x for x in transforms if cmds.objExists(x) and node_utils.is_object_type(x, ObjectType.mesh)]
    if len(mesh_transforms) > 1:
        if not name:
            name = mesh_transforms[-1]
        position = position if position else ZERO3
        parent = parent if parent else cmds.listRelatives(mesh_transforms[-1], parent=True)
        result = cmds.polyUnite(mesh_transforms, name=name, constructionHistory=history)[0]
        node_utils.set_pivot(result, value=position, reset=True)
        if parent:
            cmds.parent(result, parent)
        return result
    else:
        cmds.warning('Supply mesh nodes')


def create_cube(name: Optional[str] = None, size: float | Point3 = 1, position: Point3 = Point3(0, 0, 0),
                divisions: int = 1, baseline: float = 0) -> str:
    """
    Mirrors geometry along an axis
    :param name: str
    :param size: int
    :param position:
    :param divisions: int
    :param baseline: float
    """
    if type(size) is Point3:
        width = size.x
        height = size.y
        depth= size.z
    else:
        width = size
        height = size
        depth = size
    cube, _ = cmds.polyCube(
        name=name if name else 'cube',
        width=width, height=height, depth=depth, heightBaseline=baseline,
        sx=divisions, sy=divisions, sz=divisions)
    node_utils.set_translation(nodes=cube, value=position)
    return cube


def create_platonic_sphere(name: str, diameter: float, primitive: int = 2, subdivisions: int = 3):
    """
    Create platonic sphere
    :param name:
    :param diameter:
    :param primitive:
    :param subdivisions:
    :return:
    """
    sphere = cmds.polyPlatonic(radius=diameter / 2, primitive=primitive, subdivisionMode=0,
                               subdivisions=subdivisions, sphericalInflation=1)[0]

    return cmds.rename(sphere, name)


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
    hemispheroid = create_platonic_sphere(name=name, diameter=diameter, primitive=primitive, subdivisions=subdivisions)
    cmds.setAttr(f'{hemispheroid}.scaleY', height * 2.0 / diameter)
    cmds.makeIdentity(hemispheroid, apply=True, scale=True)

    # delete faces below y = 0
    verts_below_0 = [i for i, value in enumerate(get_vertex_positions(node=hemispheroid)) if value.y < 0]
    vert_list_by_face = get_vertex_face_list(transform=hemispheroid)
    faces_below_0 = [i for i, verts in enumerate(vert_list_by_face) for v in verts if v in verts_below_0]
    select_faces(hemispheroid, faces_below_0)
    cmds.delete(cmds.ls(sl=True))

    # create base
    if base:
        get_open_edges(hemispheroid, select=True)
        cmds.polyExtrudeEdge(cmds.ls(sl=True), scaleX=0.0, scaleZ=0.0)
        cmds.move(0, cmds.ls(sl=True), moveY=True, absolute=True)
        verts = cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True)
        cmds.polyMergeVertex(verts, distance=precision_to_threshold(diameter))

    if not construction_history:
        cmds.delete(hemispheroid, ch=True)

    node_utils.set_component_mode(ComponentType.object)

    if select:
        cmds.select(hemispheroid)
    else:
        cmds.select(clear=True)

    return hemispheroid


def detach_faces(transform: str, faces: list[int]) -> str:
    """
    Extract faces from a mesh
    :param transform:
    :param faces:
    :return:
    """
    selection = get_component_list(node=transform, indices=faces, component_type=ComponentType.face)
    children = cmds.listRelatives(transform, children=True, type=ObjectType.transform.name)

    if children:
        cmds.parent(children, world=True)

    cmds.polyChipOff(selection, duplicate=False, constructionHistory=False)
    num_shells = cmds.polyEvaluate(transform, shell=True)
    extracted, original = cmds.polySeparate(transform, separateSpecificShell=num_shells - 1,
                                            constructionHistory=False)
    detached_mesh = cmds.rename(extracted, f'{transform}_detached')
    group = cmds.listRelatives(original, parent=True, fullPath=True)[0]
    parent = cmds.listRelatives(group, parent=True, fullPath=True)
    cmds.parent(original, detached_mesh, parent)
    cmds.delete(group)
    result = cmds.rename(original, transform)

    if children:
        cmds.parent(children, result)

    node_utils.set_component_mode(ComponentType.object)
    cmds.select(detached_mesh)

    return detached_mesh

def find_geometry_by_vertices(vertex_list: list[Point3]) -> list[str]:
    """Find all geometry items that have the supplied list of vertices."""
    #print(vertex_list)
    # get a list of geometry and their bounding boxes
    geometry = node_utils.get_geometry()
    # discount items that the vertex list don't fit within
    bounds_dict = {x: node_utils.get_min_max_points(node=x) for x in node_utils.get_geometry()}
    # iterate to find matches within a tolerance
    for key, value in bounds_dict.items():
        print(f'{key}: {value}')
    filtered = [x for x in geometry if bounds_dict[x].vertices_within_bounds(vertex_list)]
    return filtered


def fix_cap(transform: str, face_id: int):
    """
    Converts an N-gon cylinder cap into a pole
    :param transform:
    :param face_id:
    """
    edges = get_edges_from_face(node=transform, face_id=face_id)
    delete_faces(transform=transform, faces=face_id)
    select_edges(transform=transform, edges=edges)
    cmds.polyExtrudeEdge(cmds.ls(sl=True), scaleX=0.0, scaleY=0.0, scaleZ=0.0)
    vertex_components = cmds.polyListComponentConversion(cmds.ls(sl=True), fromEdge=True, toVertex=True)
    vertex_ids = get_component_indices(vertex_components, component_type=ComponentType.vertex)
    merge_vertices(transform=transform, vertices=vertex_ids)


def get_component_type_tag(component_type: ComponentType) -> str or None:
    """
    Gets the tag for a component Type
    :param component_type:
    :return:
    """
    component_tag = {
        ComponentType.edge: 'e',
        ComponentType.vertex: 'vtx',
        ComponentType.face: 'f'
    }

    return component_tag.get(component_type)


def get_component_indices(component_list: list[str], component_type: ComponentType) -> list[int]:
    """
    Converts a component list to indices
    :param component_list:
    :type component_type:
    :return:
    """
    flat_list = cmds.ls(component_list, flatten=True)

    return [int(x.split(f'.{get_component_type_tag(component_type)}[')[1].split(']')[0]) for x in flat_list]


def get_component_list(node: str, indices: list[int], component_type: ComponentType):
    """
    Get a component list from a list of indices
    :param node:
    :param indices:
    :param component_type:
    :return:
    """
    return [f'{node}.{get_component_type_tag(component_type)}[{x}]' for x in indices]


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


def get_perimeter_edges_from_faces(transform: str, faces: list[int]):
    """
    Gets a list of the edges that represent the perimeter af a group of specified faces
    :param transform:
    :param faces:
    :return:
    """
    face_components = get_component_list(node=transform, indices=faces, component_type=ComponentType.face)
    all_edges = get_component_indices(cmds.polyListComponentConversion(face_components, fromFace=True, toEdge=True),
                                      component_type=ComponentType.edge)
    internal_edges = get_component_indices(
        cmds.polyListComponentConversion(face_components, fromFace=True, toEdge=True, internal=True),
        component_type=ComponentType.edge)
    return [x for x in all_edges if x not in internal_edges]


def get_faces_by_plane(transform: str, axis: Axis, value: float, threshold: float = 0.001):
    """
    Return a list of all the faces within a tolerance distance from an axial plane
    :param transform:
    :param axis:
    :param value:
    :param threshold:
    :return:
    """
    face_centers = get_face_positions(transform)
    return [i for i, position in enumerate(face_centers) if abs(position.values[axis.value] - value) < threshold]


def get_selected_edges(node: str = '') -> list[int] or None:
    """
    Gets a list of the edge ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.edge)


def get_selection() -> om.MSelectionList:
    """
    Get selected
    :return:
    """
    return om.MGlobal.getActiveSelectionList()


def get_selected_components(node: str = '', component_type: ComponentType = ComponentType.face) -> list[int] or None:
    """
    Gets a list of the component ids, or None if node not found
    :param node:
    :param component_type:
    :return:
    """
    node = node if node else node_utils.get_selected_transforms(first_only=True)
    assert component_type in (ComponentType.face, ComponentType.vertex, ComponentType.edge), 'Component not supported.'
    assert node, 'Please supply a transform.'
    assert cmds.objExists(node), 'Node does not exist.'
    component_label: dict = {ComponentType.edge: 'e', ComponentType.face: 'f', ComponentType.vertex: 'vtx'}
    state = node_utils.State()
    LOGGER.debug(f"initial component mode: {state.component_mode}")
    cmds.select(node)
    node_utils.set_component_mode(component_type=component_type)
    selection = cmds.ls(selection=True, flatten=True)
    LOGGER.debug(f"get_selected_components() - selection: {selection}")
    state.restore()
    component_prefix = f'{component_label[component_type]}['
    component_ids = [int(x.split(component_prefix)[1].split(']')[0]) for x in selection]
    return component_ids



def get_selected_faces(node: str = '') -> list[int] or None:
    """
    Gets a list of the face ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.face)


def get_selected_vertex_positions(node: str = '', convert: bool = False) -> list[Point3]:
    """Get a list of the vertex positions of the currently selected components."""
    LOGGER.debug(f"geometry_utils.get_selected_vertex_positions() -> {node}")
    node = node if node else node_utils.get_selected_transforms(full_path=True, first_only=True)
    LOGGER.debug(f"Calculated node: {node}")
    component_mode =  node_utils.get_component_mode()
    if component_mode in (ComponentType.face, ComponentType.edge) and convert:
        indices = [x.idx for x in component_utils.components_from_selection()]
        LOGGER.debug(f"selected indices: {indices}")
        vertices = get_vertices_from_faces(node=node, faces=indices)
    else:
        node_utils.set_component_mode(component_type=ComponentType.vertex)
        vertices = [x.idx for x in component_utils.components_from_selection()]
    vertex_positions = get_vertex_positions_cmds(node=node)
    return [vertex_positions[i] for i in vertices]


def get_selected_vertices(node: str = '') -> list[int] or None:
    """
    Gets a list of the face ids, or None if node not found
    :param node:
    :return:
    """
    return get_selected_components(node=node, component_type=ComponentType.vertex)


def get_vertex_count(transform: str) -> int:
    """
    Get the number of vertices in a transform
    :param transform:
    :return:
    """
    return cmds.polyEvaluate(transform, vertex=True)


def get_vertex_positions_cmds(node: str) -> list[Point3]:
    """
    Gets the position of each vertex in a mesh
    :param node:
    :return:
    """
    vertex_list = range(get_vertex_count(node))
    return [get_vertex_position(node=node, vertex_id=i) for i in vertex_list]


def get_vertex_positions(node: str, verbose: bool = False) -> om.MPointArray:
    """
    Get the vertex positions of a transform
    :param node:
    :param verbose:
    :return: om.MPointArray
    """
    vertex_iterator: om.MItMeshVertex = get_vertex_iterator(node)
    vertex_positions: list = []
    while not vertex_iterator.isDone():
        vertex_positions.append(vertex_iterator.position(om.MSpace.kWorld))
        if verbose:
            print(f"Vertex {len(vertex_positions) - 1}: {vertex_positions[-1]}")
        next(vertex_iterator)
    return vertex_positions


def get_vertex_position(node: str, vertex_id: int) -> Point3:
    """
    Get the position of a vertex or cv on a transform
    :param node:
    :param vertex_id:
    :return:
    """
    component_prefix = {'nurbsSurface': 'cv', 'mesh': 'vtx'}[node_utils.get_type_from_transform(node)]
    return Point3(*cmds.pointPosition(f'{node}.{component_prefix}[{vertex_id}]', world=True))


def set_vertex_position(transform: str, vert_id: int, position: Point3, relative=False):
    """
    Set the position of a vertex
    :param transform:
    :param vert_id:
    :param position:
    :param relative:
    """
    if relative:
        cmds.xform(f'{transform}.vtx[{vert_id}]', relative=True, translation=position.values)
    else:
        cmds.xform(f'{transform}.vtx[{vert_id}]', worldSpace=True, translation=position.values)


def get_face_positions(transform: str) -> list[Point3]:
    """
    Get the position of faces in a transform
    :param transform:
    :return:
    """
    num_faces = cmds.polyEvaluate(transform, face=True)
    return [get_face_position(transform=transform, face_id=i) for i in range(num_faces)]


def get_face_position(transform: str, face_id: int) -> Point3:
    """
    Get the position of a face in a transform
    :param transform:
    :param face_id:
    :return:
    """
    selection_list = om.MSelectionList()
    selection_list.add(f'{transform}.f[{face_id}]')
    selection_iterator = om.MItSelectionList(selection_list, om.MFn.kMeshPolygonComponent)
    dag_path, component = selection_iterator.getComponent()
    polygon_iterator = om.MItMeshPolygon(dag_path, component)
    c = None
    while not polygon_iterator.isDone():
        c = polygon_iterator.center(space=om.MSpace.kWorld)
        polygon_iterator.next()

    return Point3(c[0], c[1], c[2])


def get_vertex_face_list(transform: str) -> list[list[int]]:
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

    # So if counts was [4, 3, 5], the first 4 indices in indices
    # would be the verts for the first face. The next 3 indices
    # in indices would be the verts for the second face. The next 5
    # would belong to the third face.

    for i, count in enumerate(counts):
        # Cast to list as an om.MIntArray is the result
        out.append(list(indices[cursor: cursor + count]))
        cursor += count

    return out


def merge_vertices(transform: str, vertices: list[int] = (), threshold: float = 0.0001) -> str:
    """
    Merge vertices
    @param transform:
    @param vertices:
    @param threshold:
    @return:
    """
    if not vertices:
        vertex_components = f'{transform}.vtx[*]'
    else:
        vertex_components = get_component_list(node=transform, indices=vertices,
                                               component_type=ComponentType.vertex)

    return cmds.polyMergeVertex(vertex_components, distance=threshold)[0]


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
        select_faces(transform=transform, faces=result)
        return None
    else:
        return vertex_dict[return_type]


def get_quads(transform=None, select=False):
    """
    Get a list of triangular faces
    @param transform:
    @param select:
    """
    get_faces_by_vert_count(transform=transform, select=select, face_type='quad')


def select_vertices(transform: str, vertices: Sequence[int]):
    """
    Select vertices on a mesh
    :param transform:
    :param vertices:
    """
    cmds.select([f'{transform}.vtx[{vertex}]' for vertex in vertices])
    cmds.hilite(transform)
    cmds.selectType(vertex=True)


def select_edges(transform: str, edges: Sequence[int]):
    """
    Select faces on a mesh
    :param transform:
    :param edges:
    """
    cmds.select([f'{transform}.e[{x}]' for x in edges])
    cmds.hilite(transform)
    cmds.selectType(facet=True)


def select_faces(transform: str, faces: list[int]):
    """
    Select faces on a mesh
    :param transform:
    :param faces:
    """
    face_objects = [f'{transform}.f[{x}]' for x in faces]
    cmds.select(face_objects)
    cmds.hilite(transform)
    cmds.selectType(facet=True)


def set_edge_softness(nodes: Union[str, list[str]], angle: float = 30):
    """
    Set
    :param nodes:
    :param angle:
    """
    state = node_utils.State()
    cmds.select(nodes)
    cmds.polySoftEdge(angle=angle)
    state.restore()


def toggle_backface_culling(transforms: Optional[Sequence[str]] = None):
    """
    Toggle backface culling on passed or selected objects
    :param transforms:
    """
    transforms = list(cmds.ls(transforms)) if transforms else cmds.ls(sl=True, transforms=True)

    for item in transforms:
        value = f'{item}.backfaceCulling'
        cmds.setAttr(value, 3) if cmds.getAttr(value) == 0 else cmds.setAttr(value, 0)


def toggle_xray(transform: Optional[Sequence[str]] = None):
    """
    Toggle xray on passed or selected objects
    :param transform:
    """
    geometry_list = cmds.ls(transform) if transform else node_utils.get_selected_geometry()
    if not geometry_list:
        display_utils.warning_message(f'No geometry selected')
        return

    def toggle_xray_recursive(geometry: str):
        state = cmds.displaySurface(geometry, xRay=True, query=True)[0]
        cmds.displaySurface(geometry, xRay=not state)
        for child in node_utils.get_child_geometry(geometry):
            toggle_xray_recursive(child)

    for x in geometry_list:
        toggle_xray_recursive(geometry=x)


def get_faces_by_axis(transform: str, axis: Point3, tolerance_angle: float = 0.05) -> list[int]:
    """
    Gets the ids of faces that are facing downwards
    Increase the tolerance to pick up angled faces
    The angle between the down vector and the tolerance is arccos(down vector . tolerance vector)
    :param transform:
    :param axis:
    :param tolerance_angle:
    :return:
    """
    normals = get_face_normals(transform)
    tolerance = math.cos(degrees_to_radians(tolerance_angle))
    low, high = tolerance, 2 - tolerance

    return [idx for idx, normal in enumerate(normals) if low < dot_product(normal, axis, normalize=True) < high]


def get_face_normals(transform: str) -> list[Point3]:
    """
    Get all the face normals of a transform
    :param transform:
    :return:
    """
    rotation = Point3(*cmds.getAttr(f'{transform}.rotate')[0])

    if rotation != Point3(0, 0, 0):
        cmds.makeIdentity(transform, apply=True, rotate=True)

    poly_info = cmds.polyInfo(transform, faceNormals=True)
    result = [[float(i) for i in item.split(': ')[1].split('\n')[0].split(' ')] for item in poly_info]

    if rotation != Point3(0, 0, 0):
        node_utils.restore_rotation(transform=transform, value=rotation)

    return [normalize_vector(Point3(*x)) for x in result]


def get_face_normal(node: str, face_id: int) -> Point3:
    """
    Get the normal vector of a face
    :param node:
    :param face_id:
    :return:
    """
    rotation = Point3(*cmds.getAttr(f'{node}.rotate')[0])
    if rotation != Point3(0, 0, 0):
        cmds.makeIdentity(node, apply=True, rotate=True)
    normal = cmds.polyInfo(f'{node}.f[{face_id}]', faceNormals=True)[0]
    values = [float(x) for x in normal.split(': ')[1].split('\n')[0].split(' ')]
    if rotation != Point3(0, 0, 0):
        node_utils.restore_rotation(transform=node, value=rotation)
    return Point3(*values)


def get_vertex_positions_from_face(transform: str, face_id: int) -> dict[int, Point3]:
    """
    Get the positions of the vertices from a face
    :param transform:
    :param face_id:
    :return:
    """
    vertices = cmds.polyListComponentConversion(f'{transform}.f[{face_id}]', fromFace=True, toVertex=True)
    vertex_ids = get_ids_from_component_list(component_list=vertices, component_type=ComponentType.vertex)

    return {i: get_vertex_position(node=transform, vertex_id=i) for i in vertex_ids}


def get_ids_from_component_list(component_list: Union[str, list], component_type: ComponentType):
    """
    Extracts the component ids from a list of component transforms
    :param component_list:
    :param component_type:
    :return:
    """
    component = {
        ComponentType.vertex: '.vtx[',
        ComponentType.face: '.f[',
        ComponentType.edge: '.e['
    }[component_type]

    return [int(x.split(component)[1].split(']')[0]) for x in cmds.ls(component_list, flatten=True)]


def delete_faces(transform: str, faces: int or list[int]):
    """
    Delete a bunch of faces
    :param transform:
    :param faces:
    """
    face_list = faces if type(faces) is list else [faces]
    cmds.delete(get_component_list(node=transform, indices=face_list, component_type=ComponentType.face))


def delete_down_facing_faces(transform: str, tolerance_angle: float = 0.05):
    """
    Convenience function to delete down-facing faces
    :param transform:
    :param tolerance_angle:
    """
    down_facing = get_faces_by_axis(transform=transform, axis=NEGATIVE_Y_AXIS, tolerance_angle=tolerance_angle)

    if down_facing:
        delete_faces(transform=transform, faces=down_facing)


def get_vertices_from_face(node: str, face_id: int, as_components: bool = False) -> list[int]:
    """
    Gets the vertex ids from a face id
    :param node:
    :param face_id:
    :param as_components:
    :return:
    """
    vertices = cmds.polyListComponentConversion(f'{node}.f[{face_id}]', fromFace=True, toVertex=True)
    return vertices if as_components else get_component_indices(
        component_list=vertices, component_type=ComponentType.vertex)


def get_vertices_from_edge(node: str, edge_id: int, as_components: bool = False) -> list[int]:
    """
    Gets the vertex ids from an edge id
    :param node:
    :param edge_id:
    :param as_components:
    :return:
    """
    vertices = cmds.polyListComponentConversion(f'{node}.e[{edge_id}]', fromEdge=True, toVertex=True)

    return vertices if as_components else get_component_indices(
        component_list=vertices, component_type=ComponentType.vertex)


def get_edges_from_face(node: str, face_id: int, as_components: bool = False) -> list[int]:
    """
    Gets the edge ids from a face id
    :param node:
    :param face_id:
    :param as_components:
    :return:
    """
    edges = cmds.polyListComponentConversion(f'{node}.f[{face_id}]', fromFace=True, toEdge=True)
    return edges if as_components else get_component_indices(component_list=edges, component_type=ComponentType.edge)


def get_faces_from_edge(transform: str, edge_id: int, as_components: bool = False) -> list[int]:
    """
    Gets the faces ids from an edge id
    :param transform:
    :param edge_id:
    :param as_components:
    :return:
    """
    faces = cmds.polyListComponentConversion(f'{transform}.e[{edge_id}]', fromEdge=True, toFace=True)
    return faces if as_components else get_component_indices(component_list=faces, component_type=ComponentType.face)


def filter_face_list_by_face_normal(transform: str, faces: list[int], axis: Point3, threshold: float):
    """
    Reduce a list of faces by the dot product between their face normal and an axis
    :param transform:
    :param faces:
    :param axis:
    :param threshold:
    :return:
    """
    filtered = []
    for face_id in faces:
        normal_vector = get_face_normal(node=transform, face_id=face_id)
        dp = dot_product(vector_a=axis, vector_b=normal_vector, normalize=True)

        if 1 - dp < threshold:
            filtered.append(face_id)
    return filtered


def slice_faces(transform: str, faces: Sequence[int] = (), position: Point3 = ZERO3, axis: Axis = Axis.y):
    """
    Slice selected faces using a cutting plane
    :param transform:
    :param faces:
    :param position:
    :param axis:
    """
    if faces:
        operand = get_component_list(node=transform, indices=faces, component_type=ComponentType.face)
    else:
        operand = transform

    cmds.polyCut(operand, cutPlaneCenter=position.values, cuttingDirection=axis.name)


def get_face_above(transform: str, face_id: int) -> int or None:
    """
    Gets the connected face sharing an edge vertically above a face
    :param transform:
    :param face_id:
    :return:
    """
    edges = get_edges_from_face(node=transform, face_id=face_id)
    vertex_list = get_vertices_from_face(node=transform, face_id=face_id)
    vertex_positions = {vertex_id: get_vertex_position(node=transform, vertex_id=vertex_id) for vertex_id in
                        vertex_list}
    edge_heights = {}

    for edge in edges:
        a, b = get_vertices_from_edge(node=transform, edge_id=edge)
        edge_position = Point3Pair(vertex_positions[a], vertex_positions[b]).center
        edge_heights[edge] = edge_position.y

    top_edge = max(edge_heights, key=edge_heights.get)
    faces = get_faces_from_edge(transform=transform, edge_id=top_edge)
    faces.remove(face_id)

    return faces[0] if faces else None


def group_geometry_shells(transform: str, faces: Sequence[int]):
    """
    Groups faces in a list by poly shell
    :param transform:
    :param faces:
    :return:
    """

    @dataclass
    class IntListPair:
        a: list[int]
        b: list[int]

    vertex_face_list = get_vertex_face_list(transform)
    shells = [IntListPair([faces[0]], vertex_face_list[faces[0]])]

    for face_id in faces[1:]:
        match_found = False
        set1 = set(vertex_face_list[face_id])

        for shell in shells:
            set2 = set(shell.b)

            if len(set1.intersection(set2)):
                shell.a.append(face_id)
                shell.b.extend(vertex_face_list[face_id])
                match_found = True

        if not match_found:
            shells.append(IntListPair([face_id], vertex_face_list[face_id]))

    return [x.a for x in shells]


def get_vertices_from_faces(node: str, faces: Sequence[int]) -> list[int]:
    """
    Convert a face list to a vertex list
    :param node:
    :param faces:
    :return:
    """
    LOGGER.debug(f"node: {node}, faces: {faces}")
    face_components = get_component_list(node=node, indices=faces, component_type=ComponentType.face)
    LOGGER.debug(f"face_components: {face_components}")
    vertex_components = cmds.polyListComponentConversion(face_components, fromFace=True, toVertex=True)
    return get_component_indices(vertex_components, component_type=ComponentType.vertex)


def get_vertices_from_edges(node: str, edges: Sequence[int]) -> list[int]:
    """
    Convert a face list to a vertex list
    :param node:
    :param edges:
    :return:
    """
    edge_components = get_component_list(node=node, indices=edges, component_type=ComponentType.edge)
    vertex_components = cmds.polyListComponentConversion(edge_components, fromEdge=True, toVertex=True)
    return get_component_indices(vertex_components, component_type=ComponentType.vertex)


def get_midpoint_from_faces(transform: str, faces: Sequence[int]) -> Point3:
    """
    Finds the center of a set of faces
    :param transform:
    :param faces:
    :return:
    """
    LOGGER.debug("get_midpoint_from_faces()")
    vertices = get_vertices_from_faces(node=transform, faces=faces)
    vertex_positions = [get_vertex_position(node=transform, vertex_id=vertex) for vertex in vertices]

    return get_midpoint_from_point_list(points=vertex_positions)


def get_mesh_face_area(face_component: str) -> float:
    """Calculates the average face area of a given mesh."""
    polygon_iterator = get_polygon_iterator(face_component)
    return polygon_iterator.getArea(om.MSpace.kWorld)


def get_average_face_area(node: str) -> float:
    """Calculates the average face area of a given mesh."""
    face_areas = []

    for face_id in range(cmds.polyEvaluate(node, face=True)):
        face_area = get_mesh_face_area(f'{node}.f[{face_id}]')
        face_areas.append(face_area)

    return sum(face_areas) / len(face_areas)


def find_ngons(node: str):
    """
    Find the triangular faces in a mesh
    :param node:
    :return:
    """
    ngons: list = []
    polygon_iterator = get_polygon_iterator(node)

    while not polygon_iterator.isDone():
        face_index = polygon_iterator.index()
        edges = polygon_iterator.getEdges()

        if len(edges) > 4:
            ngons.append(face_index)

        polygon_iterator.next()

    return ngons


def find_three_edge_faces(node: str):
    """
    Find the triangular faces in a mesh
    :param node:
    :return:
    """
    three_edge_faces: list = []
    polygon_iterator = get_polygon_iterator(node)

    while not polygon_iterator.isDone():
        face_index = polygon_iterator.index()
        edges = polygon_iterator.getEdges()

        if len(edges) == 3:
            three_edge_faces.append(face_index)

        polygon_iterator.next()

    return three_edge_faces


def get_vertex_iterator(node: str) -> om.MItMeshVertex:
    """
    Get an MItMeshVertex instance from a transform
    :param node: str
    :return:
    """
    selection_list = om.MSelectionList()
    selection_list.add(node)
    dag_path, component = selection_list.getComponent(0)
    return om.MItMeshVertex(dag_path, component)


def get_edge_iterator(node: str) -> om.MItMeshEdge:
    """
    Get an MItMeshEdge instance from a transform
    :param node: str
    :return:
    """
    selection_list = om.MSelectionList()
    selection_list.add(node)
    dag_path, component = selection_list.getComponent(0)
    return om.MItMeshEdge(dag_path, component)


def get_polygon_iterator(node: str) -> om.MItMeshPolygon:
    """
    Get an MItMeshPolygon instance from a transform
    :param node: str
    :return:
    """
    selection_list = om.MSelectionList()
    selection_list.add(node)
    dag_path, component = selection_list.getComponent(0)
    return om.MItMeshPolygon(dag_path, component)


def get_face_edge_count_dict(transform: str) -> dict:
    """
    Get number of edges in each face
    :param transform:
    :return:
    """
    face_edge_dict: dict = {}
    polygon_iterator = get_polygon_iterator(node=transform)

    while not polygon_iterator.isDone():
        face_id = polygon_iterator.index()
        num_edges = len(polygon_iterator.getEdges())

        if num_edges in face_edge_dict:
            face_edge_dict[num_edges].append(face_id)
        else:
            face_edge_dict[num_edges] = [face_id]

        polygon_iterator.next()

    return face_edge_dict


def reverse_face_normals(transform: str, faces: list[int] or None = None):
    """
    Reverses the normals of specified faces
    :param transform:
    :param faces:
    """
    if faces:
        component_list = get_component_list(node=transform, indices=faces, component_type=ComponentType.face)
    else:
        component_list = f'{transform}.f[*]'

    cmds.polyNormal(component_list, normalMode=3)


def set_wireframe_color(node: str, color: RGBColor, shading: bool = True):
    """Set the wireframe color."""
    shape = node_utils.get_shape_from_transform(node=node)
    cmds.setAttr(f"{shape}.overrideEnabled", 1)
    cmds.setAttr(f"{shape}.overrideShading", 1 if shading else 0)
    cmds.setAttr(f"{shape}.overrideRGBColors", 1)
    cmds.setAttr(f"{shape}.overrideColorR", color.normalized[0])
    cmds.setAttr(f"{shape}.overrideColorG", color.normalized[1])
    cmds.setAttr(f"{shape}.overrideColorB", color.normalized[2])
