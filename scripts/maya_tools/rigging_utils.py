from maya import cmds
from typing import Optional

from core.core_enums import Axis
from core.point_classes import Point3, Point3Pair
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import get_translation, get_type_from_transform
from maya_tools.helpers import get_selected_locators, is_locator, create_locator
from maya_tools.undo_utils import UndoStack


def create_joints_from_locator_hierarchy(mirror_joints: bool = True, axis = Axis.x) -> str or None:
    """
    Build a skeleton from a hierarchy of locators
    Axis must be aligned to x with symmetry across the YZ plane
    :param mirror_joints:
    :param axis:
    :return:
    """
    selection = get_selected_locators()

    if len(selection) == 1:
        locator = selection[0]
        cmds.select(clear=True)

        with UndoStack('build_rig_from_locator_hierarchy'):
            root_joint = create_joints_recursively(locator=locator)

            if mirror_joints:
                limb_joints = get_limb_joints(joint=root_joint, root_position=get_translation(root_joint),
                                              limb_joints=[], axis=Axis.x)
                for limb_joint in limb_joints:
                    mirror_joint(joint=limb_joint, axis=axis)

            cmds.select(root_joint)

            return root_joint


def mirror_joint(joint: str, axis: Axis):
    """
    Mirror joint by axis
    :param joint:
    :param axis:
    """
    if axis is Axis.x:
        cmds.mirrorJoint(joint, mirrorYZ=True)
    elif axis is Axix.y:
        cmds.mirrorJoint(joint, mirrorXZ=True)
    else:
        cmds.mirrorJoint(joint, mirrorXY=True)


def create_locator_hierarchy_from_joints(axis: Axis = Axis.x, size: float = 2.0) -> str or None:
    """
    Build a locator hierarchy from a selected joint
    :param axis:
    :param size:
    :return:
    """
    root_joint = get_root_joint_from_selection()

    if root_joint:
        position = Point3(*cmds.xform(root_joint, query=True, worldSpace=True, translation=True))
        locator = create_locator(position=position, size=size)
        create_locators_recursively(joint=root_joint, axis=axis, parent_locator=locator, size=size)

        return locator
    else:
        cmds.warning('No joint selected.')


def create_locators_recursively(joint: str, axis: Axis, parent_locator: str, size: float):
    """
    Build the locator hierarchy recursively
    :param joint:
    :param axis:
    :param parent_locator:
    :param size:
    """
    children = cmds.listRelatives(joint, children=True, type=ObjectType.joint.name)

    if children:
        for child_joint in children:
            position = Point3(*cmds.xform(child_joint, query=True, worldSpace=True, translation=True))
            locator = create_locator(position=position, size=size)
            cmds.parent(locator, parent_locator)
            create_locators_recursively(joint=child_joint, axis=axis, parent_locator=locator, size=size)


def get_root_joint_from_selection() -> str or False:
    """
    Finds the root joint from the selection
    :return:
    """
    selection = cmds.ls(sl=True, tr=True, long=True)

    if len(selection) == 1:
        selected_transform = selection[0]
        root_node = [x for x in selected_transform.split('|') if x][0]
        root_joint = root_node if cmds.objectType(root_node) == ObjectType.joint.name else None
    else:
        root_joint = None

    return root_joint


def get_limb_joints(joint: str, root_position: Point3, axis: Axis, limb_joints: list[str],
                    tolerance: float = 0.01):
    """
    Finds the limb joints in a skeleton hierarchy
    :param joint:
    :param root_position:
    :param axis:
    :param limb_joints: supply an empty list when calling function
    :param tolerance:
    :return:
    """
    children = cmds.listRelatives(joint, children=True, type=ObjectType.transform.name)

    if children:
        for x in children:
            joint_position = Point3(*cmds.xform(x, query=True, translation=True, worldSpace=True))

            if abs(Point3Pair(joint_position, root_position).delta.values[axis.value]) > tolerance:
                limb_joints.append(x)
            else:
                get_limb_joints(joint=x, root_position=root_position, axis=axis, limb_joints=limb_joints,
                                tolerance=tolerance)

    return limb_joints


def create_joints_recursively(locator: str, parent_joint: Optional[str] = None) -> str:
    """
    Creates a rig from a hierarchy of locators
    :param locator:
    :param parent_joint:
    """
    transforms = cmds.listRelatives(locator, type=ObjectType.transform.name, children=True, fullPath=True)

    if transforms:
        locator_children = [x for x in transforms if is_locator(x)]
        position = get_translation(locator)

        if not parent_joint:
            parent_joint = cmds.joint(position=position.values)

        if locator_children:
            for locator_child in locator_children:
                child_position = Point3(*cmds.xform(locator_child, query=True, translation=True, worldSpace=True))
                cmds.select(parent_joint)
                child_joint = cmds.joint(position=child_position.values)
                create_joints_recursively(locator=locator_child, parent_joint=child_joint)

        return parent_joint


