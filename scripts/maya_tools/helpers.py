import math
from maya import cmds
from core.point_classes import Point3, Point3Pair
from core.core_enums import ComponentType
from maya_tools.geometry_utils import get_selected_vertices, get_transforms, get_vertex_position
from maya_tools.curve_utils import get_cvs
from maya_tools.node_utils import get_type_from_transform
from maya_tools.node_utils import State, set_component_mode


def place_locators_at_selected_vertices(size: float = 0.2):
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


def create_locator(position: Point3=Point3(0.0, 0.0, 0.0),  size: float = 0.2, name: str = '') -> str:
    """
    Create a space locator at a position
    :param position:
    :param size:
    :param name:
    """
    name = name if name else 'locator0'
    locator = cmds.spaceLocator(absolute=True, name=name)[0]
    cmds.setAttr(f'{locator}.translate', *position.values, type='float3')
    cmds.setAttr(f'{locator}.scale', size, size, size, type='float3')
    return locator


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
