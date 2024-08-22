import os

from functools import partial

from core.core_enums import FileExtension, Gender, Side
from maya_tools.maya_enums import ObjectType
from core.core_paths import MODELS_FOLDER, SCENES_FOLDER
from maya_tools.scene_utils import import_model, load_scene
from maya_tools.node_utils import get_root_transform, reset_pivot, delete_history, get_selected_transforms, super_reset
from maya_tools.undo_utils import UndoStack

from maya import cmds


BASE_MESH_MALE = 'base_mesh_male'
BASE_MESH_FEMALE = 'base_mesh_female'


def import_base_character(gender: Gender or str):
    """
    Import a base character
    @param gender:
    """
    gender_str = gender.name if type(gender) is Gender else gender
    file_name = f'{BASE_MESH_MALE if gender_str == "male" else BASE_MESH_FEMALE}{FileExtension.fbx.value}'
    import_path: Path = MODELS_FOLDER.joinpath(file_name)
    result = import_model(import_path=import_path)
    transform: str = next(x for x in result if cmds.objectType(x) == ObjectType.transform.name)

    if transform.startswith('|'):
        transform = transform[1:]

    cmds.select(transform)
    cmds.viewFit()

    return transform


def load_base_character(gender, latest=False):
    """
    Load a base character scene
    @param gender:
    @param latest: use this if there are multiple versioned character scenes
    """
    gender_str = gender.name if type(gender) is Gender else gender
    scene_name = BASE_MESH_MALE if gender_str == Gender.male.name else BASE_MESH_FEMALE

    if latest:
        # find all the scenes
        scenes = SCENES_FOLDER.glob(f'{scene_name}*')
        # discount the non-versioned file
        scenes = [x for x in scenes if len(str(x).split('.')) == 3]

        if not scenes:
            cmds.warning('No scenes found for {}'.format(scene_name))
            return

        # find the latest version
        scenes.sort(key=lambda x: x.split(os.sep)[-1].split('.')[1])
        scene_path = scenes[-1]
    else:
        scene_path = SCENES_FOLDER.joinpath('{}{}'.format(scene_name, FileExtension.mb.value))

    print(f'>>> Loading: {scene_path.name}')
    result = load_scene(scene_path)
    transform = next(x for x in result if cmds.objectType(x) == ObjectType.transform.name)
    cmds.select(transform)
    cmds.viewFit()
    return transform


def mirror_limbs(*args, side: Side = Side.left):
    """

    :param args:
    :param side:
    :return:
    """
    _ = args
    selected_model_node = cmds.ls(sl=True, tr=True)
    assert len(selected_model_node) == 1, 'Please select a single node'
    assert side in (Side.left, Side.right), f'Select a valid side: {side}'

    limb_nodes = get_limb_nodes(get_root_transform(selected_model_node[0]))
    og_token = side.value
    dupe_token = Side.left.value if side is Side.right else Side.right.value
    old_limbs = [x for x in limb_nodes if x.endswith(f'_{dupe_token}')]
    keepers = [x for x in limb_nodes if x not in old_limbs]
    duplicated_limbs = []

    with UndoStack('mirrorLimbs'):
        if old_limbs:
            cmds.delete(old_limbs)

        for x in keepers:
            new_group_name = f'{x[:-1]}{dupe_token}'
            dupes = cmds.duplicate(x)
            group_node = cmds.rename(dupes[0], new_group_name)
            duplicated_limbs.append(group_node)
            cmds.setAttr(f'{group_node}.scaleX', -1)
            cmds.setAttr(f'{group_node}.rotateZ', -cmds.getAttr(f'{x}.rotateZ'))
            freeze_scale_recursive(group_node)

            for child in get_child_transforms(group_node, all_children=True, full_path=True):
                old_name = child.split('|')[-1]
                new_name = old_name[:-1] if old_name.endswith(og_token) else old_name
                new_name += dupe_token
                cmds.rename(child, new_name)

    cmds.select(selected_model_node)

    return duplicated_limbs


def freeze_scale_recursive(node=None):
    children = get_child_transforms(transform=node, all_children=False, full_path=True)

    if children:
        cmds.select(children)
        cmds.parent(children, world=True)
        cmds.makeIdentity(node, apply=True, scale=True)
        cmds.parent(cmds.ls(sl=True, tr=True), node)

        for child in children:
            freeze_scale_recursive(child)


def get_child_transforms(transform: str, all_children: bool = False, full_path: bool = False) -> list[str]:
    """
    Find child transforms in a hierarchy
    :param transform:
    :param all_children:
    :param full_path:
    :return:
    """
    return cmds.listRelatives(transform, type=ObjectType.transform.name, children=True, allDescendents=all_children,
                              fullPath=full_path)


def get_limb_nodes(root_transform: str, limb_tokens: tuple[str] = ('arm', 'leg')) -> list[str] or None:
    """
    Pass a transform that is part of the model geometry
    This script finds transform nodes under the group node which contain a limb token
    :param root_transform:
    :param limb_tokens:
    :return:
    """
    group_nodes = cmds.listRelatives(root_transform, children=True, type=ObjectType.transform.name)

    if group_nodes:
        return [group for limb in limb_tokens for group in group_nodes if limb in group]


class InfoSuppression:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        cmds.scriptEditorInfo(suppressWarnings=0, suppressInfo=0, suppressErrors=0)

    def __exit__(self, *args):
        cmds.scriptEditorInfo(suppressWarnings=1, suppressInfo=1, suppressErrors=1)

