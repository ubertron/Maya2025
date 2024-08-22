import math
import pyperclip

from maya import cmds
from typing import Optional

from core.point_classes import Point3, Point3Pair
from core.core_enums import ComponentType, DataType
from maya_tools.geometry_utils import get_selected_vertices, get_transforms, get_vertex_position
from maya_tools.node_utils import get_type_from_transform, State, set_component_mode, get_selected_transforms, \
    get_pivot_position
from maya_tools.display_utils import in_view_message
from maya_tools.undo_utils import UndoStack


def create_locator(position: Point3 = Point3(0.0, 0.0, 0.0),  size: float = 1.0, name: str = '') -> str:
    """
    Create a space locator at a position
    :param position:
    :param size:
    :param name:
    """
    locator = cmds.spaceLocator(absolute=True, name=name)[0]
    cmds.setAttr(f'{locator}.translate', *position.values, type=DataType.float3.name)
    cmds.setAttr(f'{locator}.scale', size, size, size, type=DataType.float3.name)

    return locator


def create_pivot_locators(size: float = 1.0) -> list[str]:
    """
    Creates locators at the pivot position of the selected transforms
    :param size:
    """
    with UndoStack('create_pivot_locators'):
        print('size here is ', size)
        locators = [create_locator(position=get_pivot_position(x), size=size) for x in get_selected_transforms()]

    return locators


def create_vertex_locators(size: float = 0.2):
    transform = get_transforms(single=True)

    if transform:
        object_type = get_type_from_transform(transform)
        if object_type == 'mesh':
            vertex_ids = get_selected_vertices(node=transform)
        elif object_type == 'nurbsSurface':
            cmds.warning('NURBS not yet supported')
            return
        else:
            cmds.warning('No valid shape node found.')
            return

        if vertex_ids:
            for vid in vertex_ids:
                position: Point3 = get_vertex_position(transform=transform, vertex_id=vid)
                create_locator(position=position, size=size)
        else:
            cmds.warning('Please select some vertices.')
    else:
        cmds.warning('Please select some vertices on a mesh.')


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
        pm.warning(f'Pass one valid transform: {transform} [get_bounds]')
    else:
        bounding_box = cmds.exactWorldBoundingBox(transform)
        bounds = Point3Pair(Point3(*bounding_box[:3]), Point3(*bounding_box[3:]))

        if format_results:
            in_view_message(f'{transform} bounds: {bounds.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(bounds.values))

        return bounds


def get_midpoint(transform: Optional[str] = None, format_results: bool = False,
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
        pm.warning(f'Pass one valid transform: {transform} [get_midpoint]')
    else:
        midpoint = get_bounds(transform=transform).midpoint

        if format_results:
            in_view_message(f'{transform} midpoint: {midpoint.compact_repr}', persist_time=5000)

        if clipboard:
            pyperclip.copy(str(midpoint.values))

        return midpoint


def rename_selection(prefix: str, start_idx: int = 1, suffix: str = ''):
    """
    Rename selected objects
    :param prefix:
    :param start_idx:
    :param suffix:
    """
    for idx, node in enumerate(cmds.ls(sl=True, tr=True)):
        cmds.rename(node, f'{prefix}{start_idx + idx}{suffix}')


def get_selected_locators():
    """
    Gets a list of the selected locators
    :return:
    """
    return [x for x in cmds.ls(sl=True, tr=True) if is_locator(x)]


def is_locator(transform: str) -> bool:
    """
    Returns true of the supplied transform is a locator
    :param transform:
    :return:
    """
    return cmds.listRelatives(transform, type='locator') is not None


def place_locator_in_centroid(size: float = 1.0):
    """
    Creates a locator in the center of the selection
    :param size:
    """
    assert len(cmds.ls(sl=True)), 'Select geometry'
    center = get_midpoint(cmds.ls(sl=True))
    create_locator(position=center, size=size)


def auto_parent_locators():
    locators = get_selected_locators()

    if len(locators) > 1:
        for i in range(0, len(locators) - 1):
            print(locators[i])
            cmds.parent(locators[i], locators[i + 1])
