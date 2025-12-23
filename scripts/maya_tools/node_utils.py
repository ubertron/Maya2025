from __future__ import annotations

import pyperclip

from maya import cmds
from typing import Optional, Union

from core import math_utils
from core.core_enums import ComponentType, Attributes, DataType, CustomType
from core.logging_utils import get_logger
from core.point_classes import Point2, Point3, Point3Pair, ZERO3
from maya_tools import attribute_utils
from maya_tools.display_utils import warning_message, in_view_message
from maya_tools.maya_enums import ObjectType, MayaAttributes

LOGGER = get_logger(__name__)
TRANSFORMATION_ATTRS = MayaAttributes.transformation_attribute_names()


class State:
    def __init__(self):
        """
        Query and restore selection/component mode
        """
        self.component_mode = get_component_mode()
        self.selection = cmds.ls(sl=True)

        if self.is_object_mode:
            self.object_selection = cmds.ls(sl=True)
            self.component_selection = []
        else:
            self.component_selection = cmds.ls(sl=True)
            set_component_mode(ComponentType.object)
            self.object_selection = cmds.ls(sl=True)
            set_component_mode(self.component_mode)
            cmds.hilite(self.object_selection)

    def __repr__(self) -> str:
        return f'Component mode: {self.component_mode.name}\nSelection: {str(self.object_selection)}'

    def restore(self):
        """
        Set the selection and component mode as stored on init
        """
        if self.object_selection:
            cmds.select(self.object_selection, noExpand=True)
            set_component_mode(self.component_mode)
        else:
            set_component_mode(ComponentType.object)
            cmds.select(clear=True)

        if self.is_component_mode:
            cmds.select(self.component_selection)

    @property
    def is_object_mode(self) -> bool:
        return self.component_mode == ComponentType.object

    @property
    def is_component_mode(self) -> bool:
        return not self.is_object_mode

    def remove_objects(self, objects):
        """
        Sometimes necessary as cmds.objExists check causes an exception
        :param objects:
        """
        for item in [objects]:
            if item in self.object_selection:
                self.object_selection.remove(item)


def align_transform_to_joint():
    """
    Rotate a transform to match the position and orientation of a joint
    """
    transforms = get_selected_transforms()
    warning = 'Please select a joint and a single transform'

    if len(transforms) == 2:
        joints = get_selected_joints()

        if len(joints) == 1:
            joint = joints[0]
        else:
            warning_message(warning)
            return

        transform = next(x for x in transforms if x != joint)
    else:
        warning_message(warning)
        return

    orientation = cmds.joint(joint, query=True, orientation=True)
    position = get_translation(node=joint, absolute=True)
    set_translation(nodes=transform, value=position)
    set_rotation(nodes=transform, value=Point3(*orientation))


def delete(pattern: str):
    """Delete all transform nodes with the given pattern."""
    if cmds.ls(f"{pattern}*"):
        cmds.delete(f"{pattern}*")


def delete_history(nodes=None):
    """
    Delete construction history
    @param nodes:
    """
    state = State()
    set_component_mode(ComponentType.object)
    cmds.delete(cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True), constructionHistory=True)
    state.restore()


def duplicate(node: str, name: str) -> str:
    """"Duplicate a node."""
    result = cmds.duplicate(node, name=name)[0]
    super_reset(nodes=result)
    return result


def freeze_transformations(nodes: list[str] | None = None):
    """
    Freeze transformations on supplied nodes
    @param nodes:
    """
    for node in nodes if nodes else cmds.ls(sl=True, tr=True):
        lock_states = get_lock_states(node=node)
        set_lock_states(node=node, states=False)
        cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True)
        set_lock_states(node=node, states=lock_states)


def freeze_translation(node: str):
    """
    Freeze just the translation of a node
    :param node:
    :return:
    """
    cmds.makeIdentity(node, apply=True, translate=True)


def get_all_child_transforms(transform: str, ordered: bool = False, reverse: bool = False) -> list[str]:
    """
    Find all children of a transform
    Children can be transforms or joints
    :param transform:
    :param ordered:
    :param reverse:
    :return:
    """
    transform_type: str = ObjectType.transform.name
    children = cmds.listRelatives(transform, allDescendents=True, type=transform_type, fullPath=True)
    if ordered:
        children = sort_transforms_by_depth(transforms=children, reverse=reverse)
    return children if children else []


def get_all_root_transforms() -> list[str]:
    """
    @return: Finds transforms that are children of the world
    """
    return [x for x in cmds.ls(transforms=True) if not cmds.listRelatives(x, parent=True)]


def get_base_center(node: str) -> Point3:
    """Works out size respecting rotations."""
    return get_bounds(node=node, check_rotations=True).base_center


def get_bounds(node: Optional[str] = None, format_results: bool = False,
               clipboard: bool = False, check_rotations: bool = False) -> Point3Pair or None:
    """
    Get the minimum and maximum points of the bounds of a transform
    :param check_rotations:
    :param node:
    :param format_results:
    :param clipboard:
    :return:
    """
    if not node:
        node = get_transforms(first_only=True)
    if node is None:
        cmds.warning(f'Pass one valid transform: {node} [get_bounds]')
        return None
    else:
        rotation = None
        if check_rotations:
            rotation = get_rotation(node=node)
            set_rotation(nodes=node, value=ZERO3)
        bounding_box = cmds.exactWorldBoundingBox(node)
        bounds = Point3Pair(Point3(*bounding_box[:3]), Point3(*bounding_box[3:]))
        if check_rotations:
            set_rotation(nodes=node, value=rotation)
        if format_results:
            in_view_message(f'{node} bounds: {bounds.compact_repr}', persist_time=5000)
        if clipboard:
            pyperclip.copy(str(bounds.values))
        return bounds


def get_bounds_from_selection(selection_list: list | None = None) -> list[str]:
    """Get bounds from selection accounting for locators."""
    selection = cmds.ls(*selection_list) if selection_list else cmds.ls(selection=True)
    locators = [x for x in selection if is_locator(x)]
    for locator in locators:
        selection.remove(locator)
    locator_points = [get_translation(x) for x in locators]
    if locator_points:
        locator_bounds = math_utils.get_bounds_from_points(points=locator_points)
    else:
        locator_bounds = None
    bounding_box = cmds.exactWorldBoundingBox(selection) if selection else None
    if bounding_box:
        selection_bounds = Point3Pair(Point3(*bounding_box[:3]), Point3(*bounding_box[3:]))
        if locator_bounds:
            minimum_point = Point3Pair(locator_bounds, selection_bounds).minimum
            maximum_point = Point3Pair(locator_bounds, selection_bounds).maximum
            return Point3Pair(minimum_point, maximum_point)
        return selection_bounds
    return locator_bounds


def get_child_geometry(node: str) -> list[str]:
    """
    Finds all the geometry objects that are within the descendants of a transform
    :param node:
    :return:
    """
    relatives = cmds.listRelatives(node, allDescendents=True, type=ObjectType.transform.name, fullPath=True)
    if relatives:
        transforms = [x for x in relatives]
        return [x for x in transforms if is_object_type(node=x, object_type=ObjectType.mesh)]
    return []


def get_component_mode() -> ComponentType or False:
    """
    Query the component mode
    @return:
    """
    if cmds.selectMode(query=True, object=True):
        return ComponentType.object
    elif cmds.selectType(query=True, vertex=True):
        return ComponentType.vertex
    elif cmds.selectType(query=True, edge=True):
        return ComponentType.edge
    elif cmds.selectType(query=True, facet=True):
        return ComponentType.face
    elif cmds.selectType(query=True, polymeshUV=True):
        return ComponentType.uv
    else:
        return False


def get_cv_position(node: str, cv_id: int) -> Point3:
    """Gets the position of a cv."""
    return Point3(*cmds.pointPosition(f"{node}.cv[{cv_id}]"))


def get_dimensions(node: Optional[str] = None, format_results: bool = False,
                   clipboard: bool = False) -> Point3 or None:
    """
    Calculate the dimensions of a transform
    :param node:
    :param format_results:
    :param clipboard:
    """
    if not node:
        node = get_transforms(first_only=True)

    if node is None:
        cmds.warning(f'Pass one valid transform: {node} [get_dimensions]')
        return None
    else:
        dimensions = get_bounds(node=node).delta

        if format_results:
            in_view_message(f'{node} dimensions: {dimensions.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(dimensions.values))

        return dimensions


def get_geometry() -> list[str]:
    """
    Get a list of all geometry in the scene by full path.
    :return:
    """
    shapes = [x for x in cmds.ls(geometry=True) if cmds.objectType(x) == ObjectType.mesh.name]
    geometry = list({cmds.listRelatives(x, parent=True, fullPath=True)[0] for x in shapes})
    geometry.sort(key=lambda x: x.lower())
    return geometry


def get_hierarchy_depth(node: str) -> int:
    """
    Finds the number of hierarchy levels from a root transform
    :param node:
    :return:
    """
    children = get_all_child_transforms(transform=node, ordered=True, reverse=True)

    if children:
        deepest_item = get_all_child_transforms(transform=node, ordered=True, reverse=True)[0]
        tokens = [x for x in deepest_item.split('|') if x != '']

        return len(tokens)
    else:
        return 1


def get_hierarchy_path(transform: Optional[str] = None, full_path: bool = False) -> list[str] or False:
    """
    Get a list of the path of a transform from the world
    :param transform:
    :param full_path:
    :return:
    """
    warning = 'Please select a single transform'

    if transform:
        node_name = cmds.ls(transform, long=full_path)

        if node_name:
            transform = node_name[0]
        else:
            warning_message(warning)
            return False
    else:
        selection = get_selected_transforms(full_path=full_path)
        if len(selection) == 1:
            transform = selection[0]
        else:
            warning_message(text=warning)
            return False

    hierarchy = [transform]
    parent = cmds.listRelatives(transform, parent=True, fullPath=full_path)

    while parent:
        hierarchy.append(parent[0])
        parent = cmds.listRelatives(parent, parent=True, fullPath=full_path)

    return hierarchy[::-1]


def get_immediate_children(node: str) -> list[str]:
    """
    Finds the immediate children of a transform
    :param node:
    :return:
    """
    children = cmds.listRelatives(node, children=True, fullPath=True)
    return children if children else []


def get_locators() -> list[str]:
    """
    Find all the locators in the scene
    :return:
    """
    locator_shapes = cmds.ls(exactType=ObjectType.locator.name, long=True)
    return [get_transform_from_shape(shape) for shape in locator_shapes]


def get_lock_states(node: str) -> dict[str, bool]:
    """
    Get the lock states of the transformation attributes
    :param node:
    :return: dict[str, bool]
    """
    lock_states = {}
    for param in TRANSFORMATION_ATTRS:
        lock_states[param] = cmds.getAttr(f"{node}.{param}", lock=True)
    return lock_states


def get_object_component_dict(selection_list: list[str]) -> dict:
    """Converts a selection list of components into a dictionary."""
    dictionary = {}
    for x in selection_list:
        transform = x.split(".")[0]
        component_type = {
            "cv": ComponentType.cv,
            "e": ComponentType.edge,
            "f": ComponentType.face,
            "map": ComponentType.uv,
            "vtx": ComponentType.vertex,
        }[x.split(".")[1].split("[")[0]]
        idx = int(x.split("[")[1].split("]")[0])
        if transform in dictionary:
            if component_type in dictionary[transform]:
                dictionary[transform][component_type].append(idx)
            else:
                dictionary[transform][component_type] = [idx]
        else:
            dictionary[transform] = {component_type: [idx]}
    return dictionary


def get_pivot_position(transform: str) -> Point3:
    """
    Get the position of the transform's pivot
    :param transform:
    :return:
    """
    return Point3(*cmds.xform(transform, query=True, worldSpace=True, rotatePivot=True))


def get_root_transform(node: str):
    """
    Finds the top node in a hierarchy
    :param node:
    :return:
    """
    assert cmds.objExists(node), f'Transform not found: {node}'
    parent = cmds.listRelatives(node, parent=True, fullPath=True)

    return node if parent is None else get_root_transform(parent[0])


def get_object_type(node: str) -> str | None:
    if cmds.objExists(node):
        if is_group_node(node=node):
            return ObjectType.group
        if is_locator(node=node):
            return ObjectType.locator
        else:
            shape = get_shape_from_transform(node=node)
            object_type = cmds.objectType(shape)
            if object_type == ObjectType.mesh.name:
                return ObjectType.geometry
            if object_type in ('pointLight', 'directionalLight', 'ambientLight'):
                return ObjectType.light
    return None


def get_points_from_selection() -> list[Point3]:
    """Returns a list of points from locators and vertices in selection."""
    from maya_tools.geometry_utils import get_vertex_position, get_vertices_from_edge, get_vertices_from_face
    points = []
    for x in cmds.ls(selection=True, flatten=True):
        object_type = cmds.objectType(x)
        if object_type == ObjectType.mesh.name:
            node = x.split(".")[0]
            index = int(x.split("[")[1].split("]")[0])
            if ".vtx" in x:
                points.append(get_vertex_position(node=node, vertex_id=index))
            elif ".f" in x:
                vertices = get_vertices_from_face(node=node, face_id=index)
                for vertex in vertices:
                    points.append(get_vertex_position(node=node, vertex_id=vertex))
            elif ".e" in x:
                vertices = get_vertices_from_edge(node=node, edge_id=index)
                for vertex in vertices:
                    points.append(get_vertex_position(node=node, vertex_id=vertex))
        if object_type == ObjectType.nurbsCurve:
            if ".cv" in x:
                node = x.split(".")[0]
                index = int(x.split("[")[1].split("]")[0])
                points.append(get_cv_position(node=node, cv_id=index))
        elif is_locator(node=x):
            points.append(get_translation(node=x, absolute=True))
    return points


def get_root_geometry_transforms():
    """Get the root nodes of all geometry in scene."""
    return list({get_root_transform(node=x) for x in cmds.ls(type=ObjectType.mesh.name)})


def get_rotation(node: str) -> Point3:
    """
    Get the rotation of a transform
    :param node:
    :return:
    """
    return Point3(*cmds.xform(node, query=True, rotation=True, worldSpace=True))


def get_scale(node: str) -> Point3:
    """
    Get the scale of a transform
    :param node:
    :return:
    """
    return Point3(*cmds.xform(node, query=True, scale=True, worldSpace=True))


def get_selected_geometry() -> list[str]:
    """
    Get selected geometry transforms
    :return:
    """
    return [x for x in get_selected_transforms() if is_object_type(node=x, object_type=ObjectType.mesh)]


def get_selected_joints() -> list[str]:
    """
    Get selected joints
    :return:
    """
    return [x for x in get_selected_transforms() if cmds.objectType(x) == ObjectType.joint.name]


def get_selected_transforms(first_only: bool = False, full_path: bool = False) -> list[str] or str:
    """
    Get a list of selected transform nodes
    This works if in component selection mode as well as object selection mode
    :return:
    """
    state = State()
    set_component_mode(ComponentType.object)
    selection = cmds.ls(selection=True, transforms=True, long=full_path)
    state.restore()
    if selection:
        return selection[0] if first_only and selection else sorted(selection, key=lambda x: x.lower())
    else:
        return []


def get_shape_from_transform(node, full_path=False) -> str or None:
    """
    Gets the shape node if any from a transform
    Locators have unqueryable shapes
    :param node:
    :param full_path:
    :return:
    """
    object_type = cmds.objectType(node)
    if object_type == ObjectType.transform.name:
        shape_list = cmds.listRelatives(node, fullPath=full_path, shapes=True)
        return shape_list[0] if shape_list else None
    else:
        return None


def get_size(node: str, check_rotations: bool = True) -> Point3:
    """Works out size."""
    return get_bounds(node=node, check_rotations=check_rotations).size


def get_top_node(node):
    """
    Finds the top node in a hierarchy
    :param node:
    :return:
    """
    assert cmds.objExists(node), f'Node not found: {node}'
    parent = cmds.listRelatives(node, parent=True, fullPath=True)
    return node if parent is None else get_top_node(parent[0])


def get_transform_from_shape(shape: str, full_path: bool = False) -> str or False:
    """
    Gets the transform node from a shape
    :param shape:
    :param full_path:
    :return:
    """
    result = cmds.listRelatives(shape, fullPath=full_path, parent=True)
    return result[0] if result else False


def get_transforms(nodes=None, first_only: bool = False) -> list or str:
    """
    Gets the currently selected transform whether in object mode or component mode
    :param nodes:
    :param first_only:
    :return:
    """
    state = State()
    set_component_mode(ComponentType.object)
    selection = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    state.restore()
    return selection[0] if selection and first_only else selection


def get_translation(node: str, absolute: bool = False) -> Point3:
    """
    Get the translation of a transform
    :param node:
    :param absolute: use xform to calculate translation in world space
    :return:
    """
    if absolute:
        translation = cmds.xform(node, query=True, translation=True, worldSpace=True)
    else:
        translation = cmds.getAttr(f'{node}.translate')[0]
    return Point3(*translation)


def get_type_from_transform(transform: str):
    """
    Gets the type of the shape connected to a transform
    :param transform:
    :return:
    """
    return cmds.objectType(get_shape_from_transform(node=transform))


def is_boxy(node: str) -> bool:
    return attribute_utils.get_attribute(node=node, attr="custom_type") == CustomType.boxy.name


def is_geometry(node: str) -> bool:
    """Is a node a geometry node."""
    if cmds.objectType(node) == ObjectType.transform.name:
        shapes = cmds.listRelatives(node, shapes=True)
        return cmds.objectType(shapes[0]) == ObjectType.mesh.name if shapes else False
    else:
        return cmds.objectType(node) == ObjectType.mesh.name


def is_group_node(node: str):
    """
    Determine if a transform is a group node
    :param node:
    :return:
    """
    return cmds.nodeType(node) == ObjectType.transform.name and not cmds.listRelatives(node, shapes=True)


def is_locator(node: str) -> bool:
    """
    Returns true if the supplied transform is a locator
    :param node:
    :return:
    """
    return cmds.listRelatives(node, type=ObjectType.locator.name) is not None


def is_object_type(node: str, object_type: ObjectType):
    """
    Verifies an object type of a transform's corresponding shape node
    :param node:
    :param object_type:
    :return:
    """
    if object_type is ObjectType.joint:
        return cmds.objectType(node) == ObjectType.joint.name
    elif object_type is ObjectType.locator:
        return is_locator(node)
    else:
        shape = get_shape_from_transform(node)
        return cmds.objectType(shape) == object_type.name if shape else False


def is_nurbs_curve(node: str) -> bool:
    """
    Returns true if the supplied transform is a locator
    :param node:
    :return:
    """
    shape = get_shape_from_transform(node=node)
    return cmds.objectType(shape) == ObjectType.nurbsCurve.name if shape else False


def is_staircase(node: str) -> bool:
    """Is node a staircase object.

    staircase is a custom object defined in scripts/maya_tools/utilities/architools/architools.py
    """
    return cmds.attributeQuery("custom_type", node=node, exists=True) and \
        cmds.getAttr(f"{node}.custom_type") == "staircase"


def match_pivot_to_last(transforms: Optional[Union[str, list[str]]] = None):
    """
    Relocate selected pivots to the location of the pivot of the last object
    :param transforms:
    """
    selection = cmds.ls(transforms, tr=True) if transforms else cmds.ls(sl=True, tr=True)
    assert len(selection) > 1, "Please select more than one object"
    target_position = cmds.xform(selection[-1], query=True, worldSpace=True, rotatePivot=True)

    for i in range(len(selection) - 1):
        cmds.xform(selection[i], worldSpace=True, pivots=target_position)

    reset_pivot(selection[:-1])


def match_rotation():
    """Rotate selected objects to the rotation of the last selected object."""
    transforms = get_selected_transforms()
    if len(transforms) < 2:
        warning_message(text='Select more than one node')
        return
    rotation = get_rotation(node=transforms[-1])
    set_rotation(nodes=transforms[:-1], value=rotation, absolute=True)


def match_translation():
    """
    Move selected objects to the location of the last selected object
    """
    transforms = get_selected_transforms()
    if len(transforms) < 2:
        warning_message(text='Select more than one node')
        return
    location: Point3 = get_translation(node=transforms[-1], absolute=True)
    set_translation(nodes=transforms[:-1], value=location, absolute=True)


def move_to_last():
    """Move selected objects to the location of the last selected object."""
    transforms = cmds.ls(sl=True, tr=True)
    assert len(transforms) > 1, 'Select more than one node.'
    location = get_translation(node=transforms[-1], absolute=True)
    for i in range(len(transforms) - 1):
        cmds.setAttr(f'{transforms[i]}.translate', *location.values, type=DataType.float3.name)


def move_to_origin(transform=None):
    """
    Move objects to the origin
    @param transform:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.setAttr(f'{item}{Attributes.translate.value}', 0, 0, 0, type=DataType.float3.name)


def pivot_to_base(node=None, reset=True):
    """
    Send pivot to the base of the object
    @param transform:
    @param reset:
    """
    for item in [node] if node else cmds.ls(sl=True, tr=True):
        bounding_box = cmds.exactWorldBoundingBox(item)  # [x_min, y_min, z_min, x_max, y_max, z_max]
        base = [(bounding_box[0] + bounding_box[3]) / 2, bounding_box[1], (bounding_box[2] + bounding_box[5]) / 2]
        cmds.xform(item, pivots=base, worldSpace=True)

    if reset:
        reset_pivot(node)


def pivot_to_center(transform: Optional[Union[str, list[str]]] = None, reset=True):
    """
    Send pivot to the center of the object
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.xform(item, centerPivotsOnComponents=True)

    if reset:
        reset_pivot(transform)


def pivot_to_origin(transform=None, reset=True):
    """
    Send pivot to the origin
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.xform(item, piv=[0, 0, 0], ws=True)

    if reset:
        reset_pivot(transform)


def place_transform_on_ellipse(transform: str, angle: float, ellipse_radius_pair: Point2):
    """
    Translates a transform to an ellipse along the X-Y axes.
    Rotates to match the normal of the ellipse.
    :param transform:
    :param angle:
    :param ellipse_radius_pair:
    """
    position = math_funcs.get_point_position_on_ellipse(degrees=angle, ellipse_radius_pair=ellipse_radius_pair)
    angle = math_funcs.get_point_normal_angle_on_ellipse(point=position, ellipse_radius_pair=ellipse_radius_pair)
    node_utils.translate(transform, Point3(*position.values, 0))
    node_utils.rotate(transform, Point3(0, 0, angle))


def rename_transforms(transforms: Optional[list] = None, token: str = "node",
                      padding: int = 2, start: int = 1) -> list[str]:
    """
    Rename selected nodes using a token
    :param transforms:
    :param token:
    :param padding:
    :param start:
    """
    transforms = cmds.ls(transforms, tr=True) if transforms else cmds.ls(sl=True, tr=True)
    name_list = []
    for idx, x in enumerate(transforms):
        name_list.append(cmds.rename(x, f"{token}{str(idx + start).zfill(padding)}"))
    return name_list


def reset_pivot(nodes=None):
    """
    Fix transformations on the pivot so that it is relative to the origin
    @param nodes:
    """
    for node in cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True):
        lock_states = get_lock_states(node=node)
        set_lock_states(node=node, states=False)
        pivot_node = cmds.xform(node, query=True, worldSpace=True, rotatePivot=True)
        cmds.xform(node, relative=True, translation=[-i for i in pivot_node])
        cmds.makeIdentity(node, apply=True, translate=True)
        cmds.xform(node, translation=pivot_node)
        set_lock_states(node=node, states=lock_states)


def restore_rotation(transform: str, value: Point3):
    """
    Set the rotation value of a transform without rotating the object itself
    :param transform:
    :param value:
    """
    set_rotation(transform, Point3(*[-x for x in value.values]))
    cmds.makeIdentity(transform, apply=True, rotate=True)
    set_rotation(transform, value)


def scale(nodes: Union[str, list[str]], value: Point3, absolute: bool = True):
    """
    Set the scale of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.scale(*value.values, nodes, absolute=absolute)


def select_components(transform, components, component_type=ComponentType.face, hilite=True):
    """
    Select geometry components
    @param transform:
    @param components:
    @param component_type:
    @param hilite:
    """
    state = State()

    if component_type == ComponentType.vertex:
        cmds.select(transform.vtx[components])
    elif component_type == ComponentType.edge:
        cmds.select(transform.e[components])
    elif component_type == ComponentType.face:
        cmds.select(transform.f[components])
    elif component_type == ComponentType.uv:
        cmds.select(transform.map[components])
    else:
        cmds.warning('Component type not supported')

    if hilite:
        cmds.hilite(transform)
    else:
        state.restore()


def set_component_mode(component_type=ComponentType.object):
    """
    Set component mode
    @param component_type:
    """
    if component_type == ComponentType.object:
        cmds.selectMode(object=True)
    else:
        cmds.selectMode(component=True)
        if component_type == ComponentType.vertex:
            cmds.selectType(vertex=True)
        elif component_type == ComponentType.edge:
            cmds.selectType(edge=True)
        elif component_type == ComponentType.face:
            cmds.selectType(facet=True)
        elif component_type == ComponentType.uv:
            cmds.selectType(polymeshUV=True)
        else:
            cmds.warning('Unknown component type')


def set_component_mode_to_edge():
    """
    Set the component mode to edge mode
    """
    set_component_mode(ComponentType.edge)


def set_component_mode_to_face():
    """
    Set the component mode to face mode
    """
    set_component_mode(ComponentType.face)


def set_component_mode_to_object():
    """
    Set the component mode to object mode
    """
    set_component_mode(ComponentType.object)


def set_component_mode_to_uv():
    """
    Set the component mode to uv mode
    """
    set_component_mode(ComponentType.uv)


def set_component_mode_to_vertex():
    """
    Set the component mode to vertex mode
    """
    set_component_mode(ComponentType.vertex)


def set_lock_states(node: str, states: bool | dict[str, bool]):
    """Set the lock state of the transformation attributes"""
    if type(states) is bool:
        lock_states = {attr: states for attr in TRANSFORMATION_ATTRS}
    elif type(states) is dict:
        lock_states = states
    else:
        msg = f"Invalid states type: {type(states)}"
        raise TypeError(msg)
    for attr, state in lock_states.items():
        cmds.setAttr(f"{node}.{attr}", lock=state)


def set_pivot(nodes: Union[str, list[str]], value: Point3, reset: bool = False):
    """
    Set the pivot of an object
    :param nodes:
    :param value:
    :param reset:
    :return:
    """
    for node in cmds.ls(nodes):
        cmds.xform(node, worldSpace=True, pivots=value.values)
    if reset:
        reset_pivot(nodes)


def set_rotation(nodes: Union[str, list[str]], value: Point3, absolute: bool = True):
    """
    Set the rotation of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.xform(nodes, worldSpace=absolute, rotation=value.values)


def set_translation(nodes: str | list[str], value: Point3, absolute: bool = True):
    """
    Set the translation of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.move(*value.values, nodes, absolute=absolute)


def sort_transforms_by_depth(transforms: list[str], reverse: bool = False) -> list[str]:
    """
    Sorts a list of transforms by the hierarchy depth
    :param transforms:
    :param reverse:
    """
    transform_list = cmds.ls(transforms, long=True)
    transform_list.sort(key=lambda x: len(x.split('|')), reverse=reverse)
    return transform_list


def super_reset(nodes: str | list | None = None):
    """
    Reset transformations, reset pivot and delete construction history
    @param nodes:
    """
    nodes = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    freeze_transformations(nodes=nodes)
    reset_pivot(nodes=nodes)
    delete_history(nodes=nodes)
