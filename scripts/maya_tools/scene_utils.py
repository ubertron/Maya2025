import logging

from pathlib import Path
from maya import cmds
from typing import List

from core.core_enums import ComponentType


def get_scene_name(include_extension: bool = True) -> str:
    """
    Get the name of the current scene
    :param include_extension:
    :return:
    """
    scene_path = get_scene_path()

    if scene_path:
        if include_extension:
            return scene_path.name
        else:
            return '.'.join(scene_path.name.split('.')[:-1])


def get_scene_path() -> Path:
    """
    Get the full path of the scene
    :return:
    """
    return Path(cmds.file(query=True, sceneName=True))


def new_scene():
    """
    Create a new scene in Maya
    """
    cmds.file(newFile=True, force=True)


def import_model(import_path: Path):
    """
    Imports a file
    @param import_path:
    """
    return cmds.file(import_path.as_posix(), i=True, returnNewNodes=True)


def load_scene(file_path: Path, force: bool = True):
    """
    Load a scene in Maya
    @param file_path:
    @param force:
    """
    return cmds.file(file_path.as_posix(), force=force, open=True, returnNewNodes=True)


def save_scene(force: bool = False):
    """
    Perform a file save operation
    Returns false if there is no valid scene or if it is not possible to save the scene
    @param force: overwrite the path if possible
    @return:
    """
    scene_path = get_scene_path()

    if scene_path == '.':
        return False

    try:
        cmds.system.saveFile(force=force)
        return True
    except RuntimeError as err:
        logging.error(f'Please check file out in source control prior to save.: {err}')
        return False


def create_reference(file_path: Path, force: bool = False):
    """
    Creates a reference in the Maya scene
    @param file_path: str path of the source file
    @param force: bool to create reference in a new scene
    @return: cmds.system.FileReference
    """
    assert file_path.exists()

    if force:
        cmds.system.newFile(force=True)

    return cmds.system.createReference(file_path.as_posix())


class State:
    """Query and restore selection/component mode"""

    def __init__(self):
        self.component_mode = get_component_mode()
        self.selection = cmds.ls(sl=True)

        if self.object_mode:
            self.object_selection = cmds.ls(sl=True)
            self.component_selection = []
        else:
            self.component_selection = cmds.ls(sl=True)
            set_component_mode(ComponentType.object)
            self.object_selection = cmds.ls(sl=True)
            set_component_mode(self.component_mode)
            cmds.hilite(self.object_selection)

    def restore(self):
        """
        Reset the Maya scene to the last state
        """
        if self.object_selection:
            cmds.select(self.object_selection, noExpand=True)
            set_component_mode(self.component_mode)
        else:
            set_component_mode(ComponentType.object)
            cmds.select(clear=True)

        if not self.object_mode:
            cmds.select(self.component_selection)

    @property
    def object_mode(self):
        return self.component_mode is ComponentType.object

    def remove_objects(self, objects: list):
        """
        Remove objects from current selection
        Sometimes necessary as cmds.objExists check causes an exception
        @param objects:
        """
        for item in list(objects):
            if item in self.object_selection:
                self.object_selection.remove(item)


def get_component_mode() -> ComponentType or None:
    """
    Determine which component mode Maya is currently in
    @return: ComponentType or None
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
        return None


def set_component_mode(component_type: ComponentType):
    """
    Set the current Maya component mode
    @param component_type: ComponentType
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


def create_group_node(name: str, overwrite: bool = False):
    """
    Create an empty group node DAG object
    @param name:
    @param overwrite:
    @return:
    """
    if cmds.objExists(name) and overwrite:
        cmds.delete(name)

    group_node = cmds.group(name=name, empty=True)

    return group_node


def query_unsaved_changes() -> bool:
    """
    Returns True if there are unsaved changes in the current scene
    @return: bool
    """
    from maya import cmds
    return cmds.file(query=True, modified=True)


def get_top_level_transforms() -> List:
    """
    :@return: Finds transforms that are children of the world
    """
    return [x for x in cmds.ls(transforms=True) if not cmds.listRelatives(x, parent=True)]


def message_script(text: str, execute: bool = True):
    """
    Creates a script which launches an in-view message
    @param text:
    @return:
    @param execute:
    """
    if execute:
        cmds.inViewMessage(assistMessage=text, fade=True, pos="midCenter")

    return f'from maya import cmds\ncmds.inViewMessage(assistMessage="{text}", fade=True, pos="midCenter")'


