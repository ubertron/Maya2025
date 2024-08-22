import math

from random import uniform
from maya import cmds
from dataclasses import dataclass
from typing import Sequence, Union, Optional

from core.math_funcs import get_closest_position_on_line_to_point, get_average_normal_from_points, get_midpoint, \
    vector_to_euler_angles, project_point_onto_plane
from core.point_classes import Point3, Point3Pair, X_AXIS, Y_AXIS, Z_AXIS
from core.core_enums import Axis, Position, ComponentType
from maya_tools.geometry_utils import get_vertex_position, set_vertex_position, get_vertex_positions,\
    get_component_list, detach_faces
from maya_tools.node_utils import translate, rotate, get_selected_transforms
from maya_tools.helpers import get_bounds
from maya_tools.undo_utils import UndoStack


COMPONENT_LABEL: dict = {ComponentType.edge: 'e', ComponentType.face: 'f', ComponentType.vertex: 'vtx'}


def create_test_mesh():
    """
    Creates a plane with randomly shifted vertices
    """
    name = 'test_mesh'
    divisions = 5
    size = 2.0
    spacing = size / divisions
    variation = 0.6
    deviation = spacing * variation

    if cmds.objExists(name):
        cmds.delete(name)

    test_mesh, _ = cmds.polyPlane(width=size, height=size, axis=(0, 1, 0),
                                  sx=divisions, sy=divisions,
                                  name=name)

    for i in range((divisions + 1) ** 2):
        x, y, z = cmds.pointPosition(f'{test_mesh}.vtx[{i}]', world=True)
        position = [x + deviation * (uniform(0, 1) - 0.5), y, z + deviation * (uniform(0, 1) - 0.5)]
        cmds.xform(f'{test_mesh}.vtx[{i}]', worldSpace=True, translation=position)

    cmds.select(f'{test_mesh}.vtx[0:{divisions}]')


def get_selected_transform_and_vertices(warn: bool = False):
    """
    Gets the currently selected vertices and the transform they belong to
    :return:
    """
    selection = cmds.ls(sl=True, flatten=True)
    warning_message = 'Please select vertices on a single object'

    if selection:
        indices = []
        transform = selection[0].split('.')[0]

        for x in selection:
            _transform = x.split('.')[0]

            if 'vtx' not in x or _transform != transform:
                if warn:
                    cmds.warning(warning_message)
                return

            indices.append(int(x.split('vtx[')[1].split(']')[0]))

        return transform, indices
    else:
        if warn:
            cmds.warning(warning_message)
        return


def get_selected_transform_and_faces():
    """
    Gets the selected transform and any selected faces
    :return:
    """
    return get_selected_transform_and_components(component_type=ComponentType.face)


def get_selected_transform_and_components(component_type: ComponentType) -> tuple or None:
    """
    Gets the currently selected faces and the transform they belong to
    :return:
    """
    selection = cmds.ls(sl=True, flatten=True)
    warning_message = f'Please select {component_type.name} components on a single object'
    component_label: str = COMPONENT_LABEL[component_type]
    indices = []

    if selection:
        transform = selection[0].split('.')[0]

        for x in selection:
            _transform = x.split('.')[0]

            if component_label not in x or _transform != transform:
                cmds.warning(warning_message)
                return

            indices.append(int(x.split(f'{component_label}[')[1].split(']')[0]))

    return get_selected_transforms(first_only=True), indices


def align_selected_vertices(axis: int = 0, even_distribution: bool = False):
    """
    Align selected vertices along a path defined by the end point along an axis
    :param axis:
    :param even_distribution:
    """
    result = get_selected_transform_and_vertices()

    if result:
        transform, indices = result
        vertex_positions = {i: get_vertex_position(transform, i) for i in indices}
        indices.sort(key=lambda x: get_vertex_position(transform, x).values[axis])
        start = Point3(*vertex_positions[indices[0]].values)
        end = Point3(*vertex_positions[indices[-1]].values)
        spaces = len(indices) - 1

        if even_distribution:
            vector = Point3Pair(start, end).delta

            for i in range(1, spaces):
                position = Point3(*[start.values[j] + vector.values[j] / spaces * i for j in range(3)])
                set_vertex_position(transform, indices[i], position)
        else:

            for i in range(1, spaces):
                vertex_position = Point3(*vertex_positions[indices[i]])
                line = Point3Pair(start, end)
                new_position = get_closest_position_on_line_to_point(vertex_position, line)
                set_vertex_position(transform, indices[i], new_position)


def planarize_vertices(transform: str, vertices: list[int], axis: Optional[Axis] = None,
                       position: Position = Position.center):
    """
    Clamp vertices to sit on an average plane
    :param transform:
    :param vertices:
    :param position:
    :param axis:
    """
    vertex_positions = [get_vertex_position(transform=transform, vertex_id=vertex) for vertex in vertices]
    component_list = get_component_list(transform=transform, indices=vertices, component_type=ComponentType.vertex)
    bounds: Point3Pair = get_bounds(transform=component_list)

    if axis:
        if position is Position.minimum:
            value = bounds.a.values[axis.value]
        elif position is Position.maximum:
            value = bounds.b.values[axis.value]
        else:
            value = bounds.midpoint.values[axis.value]

        move_along_axis(component_list=component_list, axis=axis, value=value)
    else:
        axis: Point3 = get_average_normal_from_points(vertex_positions)
        midpoint: Point3 = bounds.midpoint

        with UndoStack('setVertices'):
            for i in range(len(vertices)):
                destination: Point3 = project_point_onto_plane(plane_position=midpoint, unit_normal_vector=axis,
                                                               point=vertex_positions[i])
                set_vertex_position(transform=transform, vert_id=vertices[i], position=destination)


def planarize_selected_vertices(axis: Optional[Axis] = None):
    """
    Convenience function to planarize vertices on selected
    :param axis:
    """
    result = get_selected_transform_and_vertices()

    if result:
        transform, indices = result
        planarize_vertices(transform=transform, vertices=indices, axis=axis)
    else:
        cmds.warning('Please select vertices on an object')


def move_along_axis(component_list: str or list, axis: Axis, value: float):
    """
    Move a component list (transforms or components) to a location along an axis
    :param component_list:
    :param axis:
    :param value:
    """
    if axis == Axis.x:
        cmds.move(value, component_list, x=True, absolute=True)
    elif axis == Axis.y:
        cmds.move(value, component_list, y=True, absolute=True)
    elif axis == Axis.z:
        cmds.move(value, component_list, z=True, absolute=True)


def detach_selected_faces() -> str or None:
    """
    Convenience function to detach selected faces
    :rtype: object
    """
    result = get_selected_transform_and_faces()

    if result:
        return detach_faces(*result)


if __name__ == '__main__':
    create_test_mesh()
    align_selected_vertices(even_distribution=True)
