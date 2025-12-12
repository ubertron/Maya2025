import pyperclip

from maya import cmds
from typing import Optional

from core.point_classes import Point3, Point3Pair
from core.core_enums import DataType, Axis
from maya_tools.geometry_utils import get_selected_vertices, get_transforms, get_vertex_position
from maya_tools.node_utils import get_type_from_transform, get_selected_transforms, \
    get_pivot_position, get_translation, get_all_child_transforms, translate, is_locator
from maya_tools.display_utils import in_view_message
from maya_tools.undo_utils import UndoStack


DEFAULT_SIZE: float = 10.0


def auto_parent_locators():
    """
    Create a locator parented hierarchy based on selection order
    """
    locators = get_selected_locators()

    if len(locators) > 1:
        for i in range(0, len(locators) - 1):
            print(locators[i])
            cmds.parent(locators[i], locators[i + 1])


def create_locator(position: Point3, name: str = "locator", size: float=DEFAULT_SIZE) -> str:
    """Create a locator."""
    result = cmds.spaceLocator()
    locator = result[0]
    new_name = cmds.rename(locator, name)
    cmds.setAttr(f"{new_name}.localScale", size, size, size, type="float3")
    cmds.setAttr(f"{new_name}.translate", *position.values, type="float3")
    return new_name


def create_pivot_locators(size: float = 1.0) -> list[str]:
    """
    Creates locators at the pivot position of the selected transforms
    :param size:
    """
    with UndoStack('create_pivot_locators'):
        print('size here is ', size)
        locators = [create_locator(position=get_pivot_position(x), size=size) for x in get_selected_transforms()]

    return locators


def create_vertex_locators(size: float = DEFAULT_SIZE) -> list[str]:
    """Create locators at the vertex positions of selected nodes."""
    locators = []
    for node in get_selected_transforms():
        object_type = get_type_from_transform(node)
        if object_type == 'mesh':
            vertex_ids = get_selected_vertices(node=node)
            if vertex_ids:
                for vid in vertex_ids:
                    position: Point3 = get_vertex_position(node=node, vertex_id=vid)
                    locators.append(create_locator(position=position, size=size))
            else:
                cmds.warning('Please select some vertices.')
    if locators:
        cmds.select(locators)
        return locators
    else:
        cmds.warning('No locators created.')
        return []


def flip_locator_hierarchy(transform: str, axis: Axis):
    """
    Flip transform positions across an axis
    :param transform:
    :param axis:
    """
    # Get all the children ordered by depth
    transforms = get_all_child_transforms(transform=transform, ordered=True, reverse=True)
    locators = [x for x in transforms if is_locator(x)]

    # Flip items along the specified axis
    with UndoStack("Move Locators"):
        for locator in locators:
            position: Point3 = get_translation(transform=locator, absolute=True)
            old_position = str(position)
            new_axis_position: float = -position.values[axis.value]

            if axis is Axis.x:
                position.x = new_axis_position
            elif axis is Axis.y:
                position.y = new_axis_position
            else:
                position.z = new_axis_position

            translate(nodes=locator, value=position, absolute=True)
            print(f"{old_position} > {position}")


def get_distance_between_two_transforms(format_result: bool = True):
    """
    Gets the distance between two transforms
    :param format_result:
    :return:
    """
    transforms = cmds.ls(sl=True, tr=True)
    if len(transforms) == 2:
        position_a = Point3(*cmds.getAttr(f'{transforms[0]}.translate')[0])
        position_b = Point3(*cmds.getAttr(f'{transforms[1]}.translate')[0])
        result = Point3Pair(a=position_a, b=position_b).length

        if format_result:
            print(f'Distance between {position_a} and {position_b} is {result}')

        return result
    else:
        cmds.warning('Please select two transforms.')
        return None


def get_dimensions(transform: Optional[str] = None, format_results: bool = False,
                   clipboard: bool = False) -> Point3 or None:
    """
    Calculate the dimensions of a transform
    :param transform:
    :param format_results:
    :param clipboard:
    """
    if not transform:
        transform = get_transforms(single=True)

    if transform is None:
        cmds.warning(f'Pass one valid transform: {transform} [get_dimensions]')
        return None
    else:
        dimensions = get_bounds(transform=transform).delta

        if format_results:
            in_view_message(f'{transform} dimensions: {dimensions.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(dimensions.values))

        return dimensions


def get_bounds(transform: Optional[str] = None, format_results: bool = False,
               clipboard: bool = False) -> Point3Pair or None:
    """
    Get the minimum and maximum points of the bounds of a transform
    :param transform:
    :param format_results:
    :param clipboard:
    :return:
    """
    if not transform:
        transform = get_transforms(single=True)

    if transform is None:
        cmds.warning(f'Pass one valid transform: {transform} [get_bounds]')
        return None
    else:
        bounding_box = cmds.exactWorldBoundingBox(transform)
        bounds = Point3Pair(Point3(*bounding_box[:3]), Point3(*bounding_box[3:]))

        if format_results:
            in_view_message(f'{transform} bounds: {bounds.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(bounds.values))

        return bounds


def get_midpoint_from_transform(transform: Optional[str] = None, format_results: bool = False,
                                clipboard: bool = False) -> Point3 or None:
    """
    Calculate the midpoint of a transform
    :param transform:
    :param format_results:
    :param clipboard:
    """
    if not transform:
        transform = get_transforms(single=True)

    if transform is None:
        cmds.warning(f'Pass one valid transform: {transform} [get_midpoint]')
        return None
    else:
        midpoint = get_bounds(transform=transform).midpoint

        if format_results:
            in_view_message(f'{transform} midpoint: {midpoint.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(midpoint.values))

        return midpoint


def get_selected_locators():
    """
    Gets a list of the selected locators
    :return:
    """
    return [x for x in cmds.ls(sl=True, tr=True) if is_locator(x)]


def place_locator_in_centroid(size: float = 1.0):
    """
    Creates a locator in the center of the selection
    :param size:
    """
    assert len(cmds.ls(sl=True)), 'Select geometry'
    center = get_midpoint_from_transform(cmds.ls(sl=True))
    create_locator(position=center, size=size)


def rename_selection(prefix: str, start_idx: int = 1, suffix: str = ''):
    """
    Rename selected objects
    :param prefix:
    :param start_idx:
    :param suffix:
    """
    for idx, node in enumerate(cmds.ls(sl=True, tr=True)):
        cmds.rename(node, f'{prefix}{start_idx + idx}{suffix}')

def zero_locator_rotations():
    selected = cmds.ls(sl=True)
    if len(selected) == 1 and selected[0] in node_utils.get_locators():
        with UndoStack("Zero Rotations"):
            zero_rotations(selected[0])
            cmds.select(selected)
    else:
        print(f"Please select a single locator")


def zero_rotations(node: str):
    children = cmds.listRelatives(node, children=True, type='transform')
    if children:
        cmds.parent(children, world=True)
        cmds.setAttr(f"{node}.rotate", 0, 0, 0, type="float3")
        cmds.parent(children, node)
        for child in children:
            zero_rotations(child)
    else:
        cmds.setAttr(f"{node}.rotate", 0, 0, 0, type="float3")