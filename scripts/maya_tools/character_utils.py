import os

from core.core_enums import FileExtension, Gender
from maya_tools.maya_enums import ObjectType
from core.core_paths import MODELS_FOLDER, SCENES_FOLDER
from maya_tools.scene_utils import import_model, load_scene

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
