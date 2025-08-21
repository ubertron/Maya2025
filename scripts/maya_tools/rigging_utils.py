import logging

from collections import OrderedDict
from maya import cmds, mel
from typing import Optional

from core.core_enums import Axis
from core.math_funcs import get_midpoint_from_point_list
from core.point_classes import Point3, Point3Pair
from maya_tools.display_utils import info_message, warning_message
from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import get_translation, get_type_from_transform, get_root_transform, is_object_type, \
    get_child_geometry, get_selected_geometry, get_selected_joints, get_selected_transforms, get_immediate_children, \
    get_all_child_transforms, get_hierarchy_depth, get_hierarchy_path, is_locator
from maya_tools.helpers import get_selected_locators, create_locator, get_midpoint_from_transform
from maya_tools.layer_utils import is_display_layer, create_display_layer, add_to_layer
from maya_tools.scene_utils import get_scene_path
from maya_tools.undo_utils import UndoStack

JOINT_LAYER: str = 'jointLayer'
JOINT_LAYER_COLOR: Point3 = Point3(0.4, 1.0, 1.0)
JOINT_SEARCH_TOLERANCE: float = 0.001


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
            warning_message(warning)
            return

        joint_hierarchy = next((x for x in selection if get_root_joint(x) is not False), None)

        if joint_hierarchy:
            joint_root = get_root_joint(joint_hierarchy)
        else:
            warning_message(warning)
            return

        model_root = next(x for x in selection if x != joint_hierarchy)

        # model validation
        geometry = get_child_geometry(transform=model_root)

        if not geometry:
            warning_message(warning)
            return

        if get_hierarchy_depth(model_root) > 2:
            warning_message('Model has invalid structure: deeply nested nodes')
            return

        if rigid_bind_mode:
            rigid_bind(model_root=model_root, joint_root=joint_root)
        else:
            cmds.bindSkin(joint_root, model_root, colorJoints=True)
    else:
        warning_message(warning)


def create_joints_from_locator_hierarchy(transform: str = "", mirror_joints: bool = False, axis: Axis = Axis.x,
                                         to_layer: bool = False) -> str or None:
    """
    Build a skeleton from a hierarchy of locators
    Axis must be aligned to x with symmetry across the YZ plane
    :param transform:
    :param mirror_joints:
    :param axis:
    :param to_layer:
    :return:
    """
    if transform:
        if is_locator(transform=transform):
            root_locator = get_root_transform(transform)
        else:
            cmds.warning('Invalid transform')
            return
    else:
        selected_locators = get_selected_locators()
        if selected_locators:
            root_locator = get_root_transform(selected_locators[0])
        else:
            cmds.warning('Invalid selection')
            return

    cmds.select(clear=True)

    with UndoStack('create_joints_from_locator_hierarchy'):
        root_joint = create_joints_recursively(locator=root_locator)

        if mirror_joints:
            limb_joints = get_limb_joints(joint=root_joint, root_position=get_translation(root_joint),
                                          limb_joints=[], axis=Axis.x)
            for limb_joint in limb_joints:
                mirror_joint(joint=limb_joint, axis=axis)

        if to_layer:
            if not is_display_layer(JOINT_LAYER):
                create_display_layer(name=JOINT_LAYER, color=JOINT_LAYER_COLOR)

            add_to_layer(transforms=root_joint, layer=JOINT_LAYER)

        reorient_joints(root_joint=root_joint, recurse=True)
        fix_root_joint_orientation(root_joint=root_joint, axis=axis)
        cmds.select(root_joint)
        return root_joint


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


def create_locator_hierarchy_from_joints(transform: str = '', mirror_joints: bool = False, axis: Axis = Axis.x,
                                         size: float = 2.0,
                                         positive_axis: bool = False) -> str or None:
    """
    Build a locator hierarchy from a selected joint
    :param transform:
    :param axis:
    :param size:
    :param mirror_joints: if set to true, we only create locators for the positive axis
    :param positive_axis: set to True if mirroring from left to right
    :return:
    """
    if not transform:
        transform = get_selected_transforms(first_only=True)
        if not transform:
            cmds.warning('Nothing selected')
            return

    if transform:
        if is_object_type(transform, object_type=ObjectType.joint):
            root_joint = get_root_joint(transform=transform)
        else:
            warning_message(f'Selection is not a joint: {transform}')
            return
    else:
        warning_message('No valid transform')
        return

    position = Point3(*cmds.xform(root_joint, query=True, worldSpace=True, translation=True))
    root_locator = create_locator(position=position, size=size)
    create_locators_recursively(joint=root_joint, axis=axis, parent_locator=root_locator, size=size,
                                mirror_joints=mirror_joints, positive_axis=positive_axis)
    cmds.select(root_locator)

    return root_locator


def create_locators_recursively(joint: str, axis: Axis, parent_locator: str, size: float, mirror_joints: bool,
                                positive_axis: bool = False):
    """
    Build the locator hierarchy recursively
    :param joint:
    :param axis:
    :param parent_locator:
    :param size:
    :param mirror_joints:
    :param positive_axis:
    """
    for child_joint in get_child_joints(joint):
        position = Point3(*cmds.xform(child_joint, query=True, worldSpace=True, translation=True))

        if mirror_joints:
            if positive_axis and position.values[axis.value] < -JOINT_SEARCH_TOLERANCE:
                continue
            elif position.values[axis.value] > JOINT_SEARCH_TOLERANCE:
                continue

        locator = create_locator(position=position, size=size)
        cmds.parent(locator, parent_locator)
        create_locators_recursively(joint=child_joint, axis=axis, parent_locator=locator, size=size,
                                    mirror_joints=mirror_joints, positive_axis=positive_axis)


def create_rigid_joint_cluster(mesh_transform: str, joint: str) -> str:
    """
    Rigid bind a mesh to a joint
    :param mesh_transform:
    :param joint:
    :return:
    """
    cluster_node = cmds.skinCluster(joint, mesh_transform, maximumInfluences=1)[0]

    return cluster_node


def export_joint_hierarchy(transform: str):
    """
    WIP
    :param transform:
    """
    scene_path: Point3 = get_scene_path()
    joint_map_path: Point3 = scene_path.parent.joinpath(f'{scene_path.stem}_joint_hierarchy.json')
    print(joint_map_path)


def fix_root_joint_orientation(root_joint: str, axis: Axis, threshold: float = 0.0001):
    """
    Set the correct orientation for the root joint
    :param root_joint:
    :param axis:
    :param threshold:
    """
    # get the children of the root joint
    children = get_child_joints(joint=root_joint)

    # select axial joint
    root_joint_position: Point3 = get_translation(transform=root_joint, absolute=True)
    axial_position = root_joint_position.values[axis.value]
    axial_joint = next((joint for joint in children if get_translation(
        joint, absolute=True).values[axis.value] - axial_position < threshold), None)

    # unparent other joints
    dismember_list = [x for x in children if x != axial_joint]
    unparented_joints = cmds.ls(cmds.parent(dismember_list, world=True), long=True)

    # reorient root joint
    reorient_joints(root_joint=root_joint, recurse=False)

    # reparent unparented joints
    cmds.parent(unparented_joints, root_joint)


def get_child_joints(joint: str, full_path: bool = False) -> list[str]:
    """
    Return a list containing child joints
    :param joint:
    :param full_path:
    :return:
    """
    joints = cmds.listRelatives(joint, children=True, type=ObjectType.joint.name, fullPath=full_path)

    return joints if joints else []


def get_end_joints(transform: str, joints=None):
    """
    Recursive function to find all the end joints under a given transform
    :param transform:
    :param joints:
    :return:
    """
    if joints is None:
        joints = []

    for child in get_immediate_children(transform):
        if get_immediate_children(child):
            get_end_joints(transform=child, joints=joints)
        else:
            joints.append(child)

    return joints


def get_influence_names_from_cluster(skin_cluster: str) -> list[str]:
    """
    Get the names of the joints for a skin cluster
    :param skin_cluster:
    :return:
    """
    return cmds.skinCluster(skin_cluster, query=True, influence=True)


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
        warning_message(f'{transform} has no skin cluster.')
        return None


def get_joint_center(joint: str) -> Point3:
    """
    Finds the center position of a joint
    :param joint:
    :return:
    """
    joint_positions: list[Point3] = [get_translation(transform=joint, absolute=True)]
    joint_positions.extend(get_translation(x, absolute=True) for x in get_child_joints(joint=joint))

    return get_midpoint_from_point_list(joint_positions)


def get_limb_joints(joint: str, root_position: Point3, axis: Axis, limb_joints: list[str]):
    """
    Finds the limb joints in a skeleton hierarchy
    :param joint:
    :param root_position:
    :param axis:
    :param limb_joints: supply an empty list when calling function
    :return:
    """
    children = cmds.listRelatives(joint, children=True, type=ObjectType.transform.name)

    if children:
        for x in children:
            joint_position = Point3(*cmds.xform(x, query=True, translation=True, worldSpace=True))

            if abs(Point3Pair(joint_position, root_position).delta.values[axis.value]) > JOINT_SEARCH_TOLERANCE:
                limb_joints.append(x)
            else:
                get_limb_joints(joint=x, root_position=root_position, axis=axis, limb_joints=limb_joints)

    return limb_joints


def get_joint_chain(joint: str, full_path: bool = False) -> list[str] or False:
    """
    Get a list of the path of a joint to the joint root
    :param joint:
    :param full_path:
    :return:
    """
    joint_name = cmds.ls(joint, long=full_path)

    if joint_name:
        if is_object_type(joint, object_type=ObjectType.joint):
            joints = [joint_name[0]]
        else:
            warning_message(f'{joint} is not a joint')
            return False
    else:
        warning_message('Invalid joint supplied')
        return False

    parent = cmds.listRelatives(joint, type=ObjectType.joint.name, parent=True, fullPath=full_path)

    while parent:
        joints.append(parent[0])
        parent = cmds.listRelatives(parent, type=ObjectType.joint.name, parent=True, fullPath=full_path)

    return joints[::-1]


def get_root_joint(transform: Optional[str] = None) -> str or False:
    """
    Find the root joint from the current selection
    One single node must be selected
    :param transform:
    :return:
    """
    selection = [transform] if transform else cmds.ls(sl=True, tr=True, long=True)

    if len(selection) != 1:
        warning_message(text='Please select a single node in a joint hierarchy')
        return False

    transform = selection[0]

    return get_joint_chain(joint=transform)[0] if cmds.objectType(transform) == ObjectType.joint.name else False


def get_skin_cluster(transform: str) -> str or None:
    """
    Finds the skin cluster nodes attached to a geometry transform
    :param transform:
    :return:
    """
    result = mel.eval(f'findRelatedSkinCluster {transform}')

    return result if result else None


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


def reorient_joints(root_joint: Optional[str] = None, recurse: bool = False):
    """
    Reorient joints
    :param root_joint:
    :param recurse:
    """
    joint_selection = cmds.ls(root_joint, type=ObjectType.joint.name) \
        if root_joint else cmds.ls(sl=True, type=ObjectType.joint.name)

    if joint_selection:
        cmds.joint(joint_selection, edit=True, orientJoint='xyz', secondaryAxisOrient='yup',
                   autoOrientSecondaryAxis=True, zeroScaleOrient=True)

        if recurse:
            for joint in joint_selection:
                for child_joint in get_child_joints(joint):
                    reorient_joints(root_joint=child_joint, recurse=True)


def restore_bind_pose():
    """
    Restore selected joint to bind pose
    """
    selection = cmds.ls(sl=True, type=ObjectType.joint.name)

    if selection and len(selection) == 1:
        cmds.dagPose(selection[0], restore=True, bindPose=True)
    else:
        warning_message('Please select a joint')


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


def rigid_bind_meshes_to_selected_joint():
    """
    Convenience function to set the skin weights for an existing skin cluster to a joint
    """
    joints = get_selected_joints()
    geometry = get_selected_geometry()
    message = 'Select geometry and a single joint.'

    if len(joints) == 1:
        joint = joints[0]
    else:
        warning_message(text=message)
        return

    if not geometry:
        warning_message(text=message)
        return

    for mesh in geometry:
        skin_cluster = get_skin_cluster(transform=mesh)

        if skin_cluster and joint in get_influence_names_from_cluster(skin_cluster=skin_cluster):
            cmds.skinPercent(skin_cluster, mesh, transformValue=[(joint, 1.0)])

    cmds.select(joint)
    logging.info(f'Meshes bound to {joint}: {", ".join(geometry)}')


def toggle_locators_joints(transform: str, mirror_joints: bool = True, axis: Axis = Axis.x, size: float = 2.0) -> str:
    """
    Toggle between joint and locator hierarchy
    :param transform:
    :param mirror_joints:
    :param axis:
    :param size:
    :return:
    """
    transform: str = get_root_transform(transform)

    if is_object_type(transform, object_type=ObjectType.locator):
        locator_root = create_joints_from_locator_hierarchy(transform=transform, mirror_joints=mirror_joints, axis=axis)
        cmds.delete(transform)
        return locator_root
    elif is_object_type(transform, object_type=ObjectType.joint):
        joint_root = create_locator_hierarchy_from_joints(transform=transform, mirror_joints=mirror_joints, axis=axis,
                                                          size=size)

        if joint_root:
            cmds.delete(transform)
            return joint_root
        else:
            warning_message('Something went wrong')
            return
    else:
        warning_message('Selection is neither a joint nor a locator')


def unbind_skin_clusters(transforms: Optional[str] = None):
    """
    Remove skin cluster nodes from selected transforms
    :param transforms:
    """
    transforms = transforms if transforms else get_selected_transforms()
    root_transforms = list(set(get_root_transform(x) for x in transforms))

    for root_transform in root_transforms:
        geometry = get_child_geometry(root_transform)

        for mesh in geometry:
            skin_cluster = get_skin_cluster(transform=mesh)

            if skin_cluster:
                cmds.skinCluster(skin_cluster, edit=True, unbind=True)

    info_message(text=f'Skin clusters removed from: {", ".join(root_transforms)}')
