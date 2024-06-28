import maya.mel as mel
import logging

from maya import cmds
from typing import Sequence, Optional, Union

from maya_tools.node_utils import get_selected_transforms
from maya_tools.maya_enums import LayerDisplayType


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

DEFAULT_LAYER: str = 'defaultLayer'
DISPLAY_LAYER: str = 'displayLayer'
REFERENCE_LAYER: str = 'referenceLayer'


def get_display_layers(nodes: Optional[list[str]] = None) -> list[str]:
    """
    get a list of the display layers
    :param nodes:
    :return:
    """
    selection = nodes if nodes else get_selected_transforms()

    return cmds.listConnections(cmds.ls(selection, tr=True)) if selection else cmds.ls(type=DISPLAY_LAYER)


def get_all_display_layers(custom_only: bool = False):
    """
    Returns a list of all display layers
    :param custom_only:
    :return:
    """
    display_layers: list = cmds.ls(type=DISPLAY_LAYER)

    if custom_only:
        display_layers.remove(DEFAULT_LAYER)

    return display_layers


def create_display_layer(name: str) -> object:
    """
    Create a new display layer with a name
    @param name:
    @return:
    """
    display_layer = next((item for item in get_all_display_layers() if item == name), None)
    return display_layer if display_layer else cmds.createDisplayLayer(name=name, empty=True)


def delete_display_layer(name):
    if name in get_all_display_layers():
        cmds.delete(name)


def add_to_layer(objects: Sequence[str], layer: str):
    """
    Add a list of objects to a layer
    :param objects:
    :param layer:
    """
    if layer not in get_all_display_layers():
        create_display_layer(layer)

    cmds.editDisplayLayerMembers(layer, objects)


def remove_from_layer(objects: Sequence[str]):
    """
    Remove a list of objects to a layer
    :param objects:
    """
    cmds.editDisplayLayerMembers(DEFAULT_LAYER, objects)


def toggle_layer_shading(layer: str):
    """
    Toggle the shading for a specified layer
    :param layer:
    """
    if isinstance(layer, str):
        layer = cmds.ls(layer)
        if layer:
            layer = layer[0]

    if layer in get_all_display_layers():
        cmds.setAttr(f'{layer}.shading', (1 - cmds.getAttr(f'{layer}.shading')))
    else:
        logging.info('Nope')


def toggle_current_layer_shading():
    """
    Toggle shading for layers representing the current object selection
    """
    for layer in get_selected_display_layers():
        toggle_layer_shading(layer)


def list_layer_contents(layer_name: str) -> list[str] or None:
    """
    Get a list of objects in a display layer
    :param layer_name:
    :return:
    """
    if layer_name in get_display_layers():
        return cmds.editDisplayLayerMembers(layer_name, query=True)


def delete_empty_layers():
    """
    Purge empty display layers
    """
    for item in get_all_display_layers():
        if not list_layer_contents(item) and item != DEFAULT_LAYER:
            delete_display_layer(item)


def add_to_reference_layer(items: Sequence[str] = ()):
    """
    Add selected objects to a reference layer
    @param items:
    """
    items = cmds.ls(items, transforms=True) if items else cmds.ls(sl=True, transforms=True)

    if len(items) > 0:
        if REFERENCE_LAYER not in get_all_display_layers():
            reference_layer = create_display_layer(REFERENCE_LAYER)
            cmds.setAttr(reference_layer.shading, False)
            cmds.setAttr(reference_layer.displayType, 2)

        add_to_layer(items, REFERENCE_LAYER)


def get_selected_display_layers():
    layers = mel.eval('getLayerSelection("Display")')
    return [item for item in get_all_display_layers() if item in layers]


def set_display_layer_color(display_layer, color):
    cmds.setAttr(display_layer.overrideColorRGB, [i / 255.0 for i in color])
    cmds.setAttr(display_layer.overrideRGBColors, True)


def get_layer_display_types(custom_only: bool = False) -> dict:
    """
    Gets a dict of layer names and their respective display types
    :return:
    """
    return {layer: LayerDisplayType.get_by_value(cmds.getAttr(f'{layer}.displayType'))
            for layer in get_all_display_layers(custom_only=custom_only)}


def set_layer_display_type(layer: str, layer_display_type: Union[int, LayerDisplayType]):
    """
    Set a layer display type
    :param layer:
    :param layer_display_type:
    """
    value = layer_display_type if type(layer) is int else layer_display_type.value
    cmds.setAttr(f'{layer}.displayType', value)
