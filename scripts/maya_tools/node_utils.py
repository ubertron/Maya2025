from maya import cmds
from typing import Optional, Union

from core.point_classes import Point2, Point3, Point3Pair
from core.core_enums import ComponentType, Attr, DataType
from maya_tools.maya_enums import ObjectType
from maya_tools.display_utils import warning_message


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
    position = get_translation(transform=joint, absolute=True)
    translate(nodes=transform, value=position)
    rotate(nodes=transform, value=Point3(*orientation))


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


def get_child_geometry(transform: str) -> list[str]:
    """
    Finds all the geometry objects that are within the descendants of a transform
    :param transform:
    :return:
    """
    relatives = cmds.listRelatives(transform, allDescendents=True, type=ObjectType.transform.name,  fullPath=True)
    if relatives:
        transforms = [x for x in relatives]
        return [x for x in transforms if is_object_type(transform=x, object_type=ObjectType.mesh)]
    return []


def get_hierarchy_depth(transform: str) -> int:
    """
    Finds the number of hierarchy levels from a root transform
    :param transform:
    :return:
    """
    children = get_all_child_transforms(transform=transform, ordered=True, reverse=True)

    if children:
        deepest_item = get_all_child_transforms(transform=transform, ordered=True, reverse=True)[0]
        tokens = [x for x in deepest_item.split('|') if x != '']

        return len(tokens)
    else:
        return 1


def get_immediate_children(transform: str) -> list[str]:
    """
    Finds the immediate children of a transform
    :param transform:
    :return:
    """
    children = cmds.listRelatives(transform, children=True, fullPath=True)
    return children if children else []


def get_locators() -> list[str]:
    """
    Find all the locators in the scene
    :return:
    """
    locator_shapes = cmds.ls(exactType=ObjectType.locator.name, long=True)

    return [get_transform_from_shape(shape) for shape in locator_shapes]


def get_pivot_position(transform: str) -> Point3:
    """
    Get the position of the transform's pivot
    :param transform:
    :return:
    """
    return Point3(*cmds.xform(transform, query=True, worldSpace=True, rotatePivot=True))


def get_root_transform(transform: str):
    """
    Finds the top node in a hierarchy
    :param transform:
    :return:
    """
    assert cmds.objExists(transform), f'Transform not found: {transform}'
    parent = cmds.listRelatives(transform, parent=True, fullPath=True)

    return transform if parent is None else get_root_transform(parent[0])


def get_all_root_transforms() -> list[str]:
    """
    @return: Finds transforms that are children of the world
    """
    return [x for x in cmds.ls(transforms=True) if not cmds.listRelatives(x, parent=True)]


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


def set_component_mode_to_vertex():
    """
    Set the component mode to vertex mode
    """
    set_component_mode(ComponentType.vertex)


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


def delete_history(nodes=None):
    """
    Delete construction history
    @param nodes:
    """
    state = State()
    set_component_mode(ComponentType.object)
    cmds.delete(cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True), constructionHistory=True)
    state.restore()


def freeze_transformations(nodes=None):
    """
    Freeze transformations on supplied nodes
    @param nodes:
    """
    for node in [nodes] if nodes else cmds.ls(sl=True, tr=True):
        cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True)


def reset_pivot(nodes=None):
    """
    Fix transformations on the pivot so that it is relative to the origin
    @param nodes:
    """
    for item in cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True):
        pivot_node = cmds.xform(item, query=True, worldSpace=True, rotatePivot=True)
        cmds.xform(item, relative=True, translation=[-i for i in pivot_node])
        cmds.makeIdentity(item, apply=True, translate=True)
        cmds.xform(item, translation=pivot_node)


def super_reset(nodes=None):
    """
    Reset transformations, reset pivot and delete construction history
    @param nodes:
    """
    nodes = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    freeze_transformations(nodes)
    reset_pivot(nodes)
    delete_history(nodes)


def pivot_to_base(transform=None, reset=True):
    """
    Send pivot to the base of the object
    @param transform:
    @param reset:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        bounding_box = cmds.exactWorldBoundingBox(item)  # [x_min, y_min, z_min, x_max, y_max, z_max]
        base = [(bounding_box[0] + bounding_box[3]) / 2, bounding_box[1], (bounding_box[2] + bounding_box[5]) / 2]
        cmds.xform(item, piv=base, ws=True)

    if reset:
        reset_pivot(transform)


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


def move_to_origin(transform=None):
    """
    Move objects to the origin
    @param transform:
    """
    for item in [transform] if transform else cmds.ls(sl=True, tr=True):
        cmds.setAttr(f'{item}{Attr.translate.value}', 0, 0, 0, type=DataType.float3.name)


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


def get_selected_geometry() -> list[str]:
    """
    Get selected geometry transforms
    :return:
    """
    return [x for x in get_selected_transforms() if is_object_type(transform=x, object_type=ObjectType.mesh)]


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
    selection = cmds.ls(sl=True, tr=True, long=full_path)
    state.restore()
    if selection:
        return selection[0] if first_only and selection else selection
    else:
        return []


def get_transforms(nodes=None, first_only: bool = False) -> list or str:
    state = State()
    set_component_mode(ComponentType.object)
    selection = cmds.ls(nodes, tr=True) if nodes else cmds.ls(sl=True, tr=True)
    state.restore()
    return selection[0] if selection and first_only else selection


def get_shape_from_transform(transform, full_path=False) -> str or None:
    """
    Gets the shape node if any from a transform
    Locators have unqueryable shapes
    :param transform:
    :param full_path:
    :return:
    """
    object_type = cmds.objectType(transform)
    if cmds.listRelatives(transform, type=ObjectType.locator.name):
        return None
    if object_type == ObjectType.transform.name:
        shape_list = cmds.listRelatives(transform, fullPath=full_path, shapes=True)
        return shape_list[0] if shape_list else None
    else:
        return None


def get_transform_from_shape(shape: str, full_path: bool = False) -> str or False:
    """
    Gets the transform node from a shape
    :param shape:
    :param full_path:
    :return:
    """
    result = cmds.listRelatives(shape, fullPath=full_path, parent=True)
    return result[0] if result else False


def get_type_from_transform(transform: str):
    """
    Gets the type of the shape connected to a transform
    :param transform:
    :return:
    """
    return cmds.objectType(get_shape_from_transform(transform=transform))


def is_group_node(transform: str):
    """
    Determine if a transform is a group node
    :param transform:
    :return:
    """
    return cmds.nodeType(transform) == ObjectType.transform.name and not cmds.listRelatives(transform, shapes=True)


def is_locator(transform: str) -> bool:
    """
    Returns true of the supplied transform is a locator
    :param transform:
    :return:
    """
    return cmds.listRelatives(transform, type=ObjectType.locator.name) is not None


def is_object_type(transform: str, object_type: ObjectType):
    """
    Verifies an object type of a transform's corresponding shape node
    :param transform:
    :param object_type:
    :return:
    """
    if object_type is ObjectType.joint:
        return cmds.objectType(transform) == ObjectType.joint.name
    elif object_type is ObjectType.locator:
        return is_locator(transform)
    else:
        shape = get_shape_from_transform(transform)
        return cmds.objectType(shape) == object_type.name if shape else False


def match_rotation():
    """Rotate selected objects to the rotation of the last selected object."""
    transforms = get_selected_transforms()
    if len(transforms) < 2:
        warning_message(text='Select more than one node')
        return
    rotation = get_rotation(transform=transforms[-1])
    rotate(nodes=transforms[:-1], value=rotation, absolute=True)


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


def move_to_last():
    """Move selected objects to the location of the last selected object."""
    transforms = cmds.ls(sl=True, tr=True)
    assert len(transforms) > 1, 'Select more than one node.'
    location = get_translation(transform=transforms[-1], absolute=True)
    for i in range(len(transforms) - 1):
        cmds.setAttr(f'{transforms[i]}.translate', *location.values, type=DataType.float3.name)


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


def match_translation():
    """
    Move selected objects to the location of the last selected object
    """
    transforms = get_selected_transforms()
    if len(transforms) < 2:
        warning_message(text='Select more than one node')
        return
    location: Point3 = get_translation(transform=transforms[-1], absolute=True)
    translate(nodes=transforms[:-1], value=location, absolute=True)


def translate(nodes: Union[str, list[str]], value: Point3, absolute: bool = True):
    """
    Set the translation of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.move(*value.values, nodes, absolute=absolute)


def rotate(nodes: Union[str, list[str]], value: Point3, absolute: bool = True):
    """
    Set the rotation of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.rotate(*value.values, nodes, absolute=absolute)


def scale(nodes: Union[str, list[str]], value: Point3, absolute: bool = True):
    """
    Set the scale of passed nodes
    :param nodes:
    :param value:
    :param absolute:
    """
    cmds.scale(*value.values, nodes, absolute=absolute)


def get_translation(transform: str, absolute: bool = False) -> Point3:
    """
    Get the translation of a transform
    :param transform:
    :param absolute: use xform to calculate translation in world space
    :return:
    """
    if absolute:
        translation = cmds.xform(transform, query=True, translation=True, worldSpace=True)
    else:
        translation = cmds.getAttr(f'{transform}.translate')[0]

    return Point3(*translation)


def get_rotation(transform: str) -> Point3:
    """
    Get the rotation of a transform
    :param transform:
    :return:
    """
    return Point3(*cmds.getAttr(f'{transform}.rotate')[0])


def get_scale(transform: str) -> Point3:
    """
    Get the scale of a transform
    :param transform:
    :return:
    """
    return Point3(*cmds.getAttr(f'{transform}.scale')[0])


def restore_rotation(transform: str, value: Point3):
    """
    Set the rotation value of a transform without rotating the object itself
    :param transform:
    :param value:
    """
    rotate(transform, Point3(*[-x for x in value.values]))
    cmds.makeIdentity(transform, apply=True, rotate=True)
    rotate(transform, value)


def set_pivot(nodes: Union[str, list[str]], value: Point3, reset: bool = False):
    for node in cmds.ls(nodes):
        cmds.xform(node, worldSpace=True, pivots=value.values)

    if reset:
        reset_pivot(nodes)


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


def get_top_node(node):
    """
    Finds the top node in a hierarchy
    :param node:
    :return:
    """
    assert cmds.objExists(node), f'Node not found: {node}'
    parent = cmds.listRelatives(node, parent=True, fullPath=True)

    return node if parent is None else get_top_node(parent[0])


def sort_transforms_by_depth(transforms: list[str], reverse: bool = False) -> list[str]:
    """
    Sorts a list of transforms by the hierarchy depth
    :param transforms:
    :param reverse:
    """
    transform_list = cmds.ls(transforms, long=True)
    transform_list.sort(key=lambda x: len(x.split('|')), reverse=reverse)

    return transform_list