"""
save_project_definition(): saves the ProjectDefinition instance to the project root as a .ams file
load_project_definition(): loads the ProjectDefinition instance from the project root .ams file
---
Potential further definitions:
- Maya scene file format
"""

import pickle

from pathlib import Path

from maya_tools.ams.project_definition import ProjectDefinition
from core.core_enums import FileExtension


class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == '__main__':
            module = 'maya_tools.ams.project_utils'

        return super().find_class(module, name)


def save_project_definition(project_definition: ProjectDefinition, project_root: Path):
    """
    Save a project definition to the project root
    :param project_definition:
    :param project_root:
    """
    pickle.dump(project_definition, open(project_root.joinpath(FileExtension.ams.value), 'wb'))


def load_project_definition(project_root: Path) -> ProjectDefinition or None:
    """
    Loads a project definition from file
    :param project_root:
    :return:
    """
    assert project_root.exists(), 'Cannot find project'
    project_definition_path = project_root.joinpath(FileExtension.ams.value)

    if project_definition_path.exists():
        with open(project_definition_path.as_posix(), 'rb') as f:
            unpickler = CustomUnpickler(f)
            result = unpickler.load()
            return result
    else:
        return None


def get_current_project_root(file_path: Path) -> Path or None:
    """
    Looks for a .ams file in a parent folder of the passed file_path to deduce the project root
    :param file_path: 
    :return: 
    """
    parent_dir = file_path.parent

    if parent_dir != Path('.'):
        while len(parent_dir.parts) > 2:
            search_path: Path = parent_dir.joinpath('.ams')

            if search_path.exists():
                return parent_dir
            elif search_path.parent is None:
                return None
            else:
                parent_dir = parent_dir.parent


def get_project_definition(file_path: Path) -> ProjectDefinition or None:
    """
    Deduce the project definition while having a scene file loaded
    :return:
    """
    project_root = get_current_project_root(file_path=file_path)

    if project_root:
        return load_project_definition(project_root=project_root)


if __name__ == '__main__':
    from core.core_enums import Platform, Engine, AssetType

    animation_sandbox = Path('/Users/andrewdavis/Dropbox/Projects/Unity/AnimationSandbox')

    my_project_definition = ProjectDefinition(
        root=animation_sandbox,
        platform=Platform(engine=Engine.unity, version='2021.3.9f1'),
        materials=Path('Assets/Materials'),
        exports=Path('Assets/Models'),
        scenes=Path('Assets/Scenes'),
        textures=Path('Assets/Textures'),
        source_art=Path('SourceArt'),
    )

    # save_project_definition(project_definition=my_project_definition, project_root=animation_sandbox)
    loaded_definition: ProjectDefinition = load_project_definition(project_root=animation_sandbox)
    print(loaded_definition, loaded_definition.root)
    print(loaded_definition.get_asset_export_folder('clairee', asset_type=AssetType.character, schema=('Cat', 'Female')))
