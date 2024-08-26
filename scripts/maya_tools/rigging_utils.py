import logging

from collections import OrderedDict
from maya import cmds, mel
from typing import Optional

from core.core_enums import Axis
from core.math_funcs import get_midpoint_from_point_list
from core.point_classes import Point3, Point3Pair
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import get_translation, get_type_from_transform, get_root_transform, is_object_type, \
    get_child_geometry, get_selected_geometry, get_selected_joints
from maya_tools.helpers import get_selected_locators, is_locator, create_locator, get_midpoint_from_transform
from maya_tools.layer_utils import is_display_layer, create_display_layer, add_to_layer
from maya_tools.undo_utils import UndoStack

JOINT_LAYER: str = 'jointLayer'
JOINT_LAYER_COLOR: Point3 = Point3(0.4, 1.0, 1.0)


def create_joints_from_locator_hierarchy(mirror_joints: bool = False, axis: Axis = Axis.x) -> str or None:
    """
    Build a skeleton from a hierarchy of locators
    Axis must be aligned to x with symmetry across the YZ plane
    :param mirror_joints:
    :param axis:
    :return:
    """
    selection = get_selected_locators()

    if len(selection) == 1:
        root_locator = get_root_transform(selection[0])
        cmds.select(clear=True)

        with UndoStack('build_rig_from_locator_hierarchy'):
            root_joint = create_joints_recursively(locator=root_locator)

            if mirror_joints:
                limb_joints = get_limb_joints(joint=root_joint, root_position=get_translation(root_joint),
                                              limb_joints=[], axis=Axis.x)
                for limb_joint in limb_joints:
                    mirror_joint(joint=limb_joint, axis=axis)

            if not is_display_layer(JOINT_LAYER):
                create_display_layer(name=JOINT_LAYER, color=JOINT_LAYER_COLOR)

            add_to_layer(transforms=root_joint, layer=JOINT_LAYER)
            cmds.select(root_joint)

            return root_joint


def get_influences(transform: str, threshold: float = 0.01, select: bool = False) -> str or None:
    """
    Get a list of influence objects related to an object's skin cluster
    :param transform:
    :param threshold:
    :param select:
    :return:
    """
    skin_cluster = get_skin_cluster(transform=transform)

    if skin_cluster:
        influences = get_influence_names_from_cluster(skin_cluster=skin_cluster)
        skin_weights = get_skin_weights(transform=transform)
        output_list = [val for idx, val in enumerate(influences) for sws in skin_weights if sws[idx] > threshold]
        output_list = list(set(output_list))

        if select:
            cmds.select(output_list)

        return output_list
    else:
        cmds.warning(f'{transform} has no skin cluster.')
        return None


def get_influence_names_from_cluster(skin_cluster: str) -> list[str]:
    """
    Get the names of the joints for a skin cluster
    :param skin_cluster:
    :return:
    """
    return cmds.skinCluster(skin_cluster, query=True, influence=True)


def get_skin_weights(transform: str) -> list[list[float]] or None:
    """
    Get a list of skin weights for each vertex in a transform
    :param transform:
    :return:
    """
    skin_cluster = get_skin_cluster(transform=transform)
    skin_weights = []

    if skin_cluster:

        for i in range(cmds.polyEvaluate(transform, vertex=True)):
            skin_weights.append(cmds.skinPercent(skin_cluster, f'{transform}.vtx[{i}]', query=True, value=True))

        return skin_weights


def get_skin_cluster(transform: str) -> str or None:
    """
    Finds the skin cluster nodes attached to a geometry transform
    :param transform:
    :return:
    """
    result = mel.eval(f'findRelatedSkinCluster {transform}')

    return result if result else None


def mirror_joint(joint: str, axis: Axis):
    """
    Mirror joint by axis
    :param joint:
    :param axis:
    """
    if axis is Axis.x:
        cmds.mirrorJoint(joint, mirrorYZ=True)
    elif axis is Axis.y:
        cmds.mirrorJoint(joint, mirrorXZ=True)
    else:
        cmds.mirrorJoint(joint, mirrorXY=True)


def create_locator_hierarchy_from_joints(axis: Axis = Axis.x, size: float = 2.0,
                                         mirror_joints: bool = False) -> str or None:
    """
    Build a locator hierarchy from a selected joint
    :param axis:
    :param size:
    :param mirror_joints: if set to true, we only create locators for the positive axis
    :return:
    """
    root_joint = get_root_joint_from_selection()

    if root_joint:
        position = Point3(*cmds.xform(root_joint, query=True, worldSpace=True, translation=True))
        locator = create_locator(position=position, size=size)
        create_locators_recursively(joint=root_joint, axis=axis, parent_locator=locator, size=size,
                                    mirror_joints=mirror_joints)
        cmds.select(locator)

        return locator
    else:
        cmds.warning('No joint selected.')


def get_child_joints(joint: str) -> list[str]:
    """
    Return a list containing child joints
    :param joint:
    :return:
    """
    joints = cmds.listRelatives(joint, children=True, type=ObjectType.joint.name)
    return joints if joints else []


def create_locators_recursively(joint: str, axis: Axis, parent_locator: str, size: float, mirror_joints: bool):
    """
    Build the locator hierarchy recursively
    :param joint:
    :param axis:
    :param parent_locator:
    :param size:
    :param mirror_joints:
    """
    for child_joint in get_child_joints(joint):
        position = Point3(*cmds.xform(child_joint, query=True, worldSpace=True, translation=True))

        if mirror_joints and position.values[axis.value] < 0:
            continue

        locator = create_locator(position=position, size=size)
        cmds.parent(locator, parent_locator)
        create_locators_recursively(joint=child_joint, axis=axis, parent_locator=locator, size=size,
                                    mirror_joints=mirror_joints)


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


def orient_joints(joint_root: Optional[str] = None, recurse: bool = False):
    """
    Orient joints
    :param joint_root:
    :param recurse:
    """
    joint_selection = cmds.ls(joint_root, type=ObjectType.joint.name) \
        if joint_root else cmds.ls(sl=True, type=ObjectType.joint.name)

    if joint_selection:
        cmds.joint(joint_selection, edit=True, orientJoint='xyz', secondaryAxisOrient='yup',
                   autoOrientSecondaryAxis=True, zeroScaleOrient=True)

        if recurse:
            for joint in joint_selection:
                for child_joint in get_child_joints(joint):
                    orient_joints(joint_root=child_joint, recurse=True)


def bind_skin(rigid_bind_mode: bool = False):
    """
    Bind a model hierarchy to a skeleton
    Select the root of the geometry and the skeleton to make this happen
    :return:
    """
    warning = 'Please select model root and joint root.'
    selection = cmds.ls(sl=True, tr=True)

    if len(selection) == 2:
        if False in [not cmds.listRelatives(x, parent=True) for x in selection]:
            cmds.warning(warning)
            return

        # find joint root
        joint_root = next((x for x in selection if cmds.objectType(x) == ObjectType.joint.name), None)

        if not joint_root:
            cmds.warning(warning)
            return

        # check model root for geometry
        model_root = next(x for x in selection if x != joint_root)
        geometry = get_child_geometry(transform=model_root)

        if not geometry:
            cmds.warning(warning)
            return

        # bind operation
        # TODO: validate the model to ensure it is flat and has reset transformations

        if rigid_bind_mode:
            rigid_bind(model_root=model_root, joint_root=joint_root)
        else:
            cmds.bindSkin(joint_root, model_root, colorJoints=True)
    else:
        cmds.warning(warning)


def restore_bind_pose():
    """
    Restore selected joint to bind pose
    """
    selection = cmds.ls(sl=True, type=ObjectType.joint.name)

    if selection and len(selection) == 1:
        cmds.dagPose(selection[0], restore=True, bindPose=True)
    else:
        cmds.warning('Please select a joint')


def rigid_bind(model_root: str, joint_root: str):
    """
    Bind a model to a skeleton with single joint influence
    Locks to the closest bone on a per-object basis
    There may be incorrect assumptions, so check all bones
    :param model_root:
    :param joint_root:
    """
    # get the geometric center of each joint
    joint_type = ObjectType.joint.name
    joint_positions = {x: get_joint_center(x) for x in cmds.listRelatives(joint_root, allDescendents=True,
                                                                          fullPath=True, type=joint_type)}

    # iterate through geometry and find the closest joint to each mesh
    geometry = get_child_geometry(transform=model_root)

    for mesh in geometry:
        position = get_midpoint_from_transform(transform=mesh)
        joint, _ = min(joint_positions.items(), key=lambda item: Point3Pair(position, item[1]).length)
        logging.debug(f'Closest joint to {mesh} is {joint}')

        # set the skin weights automatically
        cluster_node = create_rigid_joint_cluster(mesh_transform=mesh, joint=joint)
        cmds.skinPercent(cluster_node, mesh, transformValue=[(joint, 1.0)])


def create_rigid_joint_cluster(mesh_transform: str, joint: str) -> str:
    """
    Rigid bind a mesh to a joint
    :param mesh_transform:
    :param joint:
    :return:
    """
    cluster_node = cmds.skinCluster(joint, mesh_transform, maximumInfluences=1)[0]

    return cluster_node


def rigid_bind_meshes_to_selected_joint():
    """
    Convenience function to set the skin weights for an existing skin cluster to a joint
    """
    joints = get_selected_joints()
    geometry = get_selected_geometry()

    if len(joints) == 1:
        joint = joints[0]
    else:
        cmds.warning('Please select a single joint.')
        return

    if not geometry:
        cmds.warning('Please select geometry.')
        return

    for mesh in geometry:
        skin_cluster = get_skin_cluster(transform=mesh)

        if skin_cluster and joint in get_influence_names_from_cluster(skin_cluster=skin_cluster):
            cmds.skinPercent(skin_cluster, mesh, transformValue=[(joint, 1.0)])

    logging.info(f'Meshes bound to {joint}: {", ".join(geometry)}')


def get_joint_center(joint: str) -> Point3:
    """
    Finds the center position of a joint
    :param joint:
    :return:
    """
    joint_positions: list[Point3] = [get_translation(transform=joint, absolute=True)]
    joint_positions.extend(get_translation(x, absolute=True) for x in get_child_joints(joint=joint))

    return get_midpoint_from_point_list(joint_positions)
