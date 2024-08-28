import maya.mel as mel
import logging

from maya import cmds
from typing import Sequence, Optional, Union

from maya_tools.node_utils import get_selected_transforms
from maya_tools.maya_enums import LayerDisplayType, ObjectType
from core.point_classes import Point3


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

DEFAULT_LAYER: str = 'defaultLayer'
REFERENCE_LAYER: str = 'referenceLayer'


def add_to_layer(transforms: Sequence[str] or str, layer: str):
    """
    Add a list of objects to a layer
    :param transforms:
    :param layer:
    """
    if layer not in get_display_layers():
        create_display_layer(layer)

    cmds.editDisplayLayerMembers(layer, transforms)


def create_display_layer(name: str, color: Optional[Point3]) -> str:
    """
    Create a new display layer with a name
    @param name:
    @param color:
    @return:
    """
    display_layer = next((item for item in get_display_layers() if item == name), None)

    if not display_layer:
        display_layer = cmds.createDisplayLayer(name=name, empty=True)

    if color:
        set_display_layer_color(display_layer=display_layer, color=color)

    return display_layer


def delete_display_layer(layer_name: str):
    """
    Delete a display layer
    :param layer_name:
    """
    if is_display_layer(layer_name):
        cmds.delete(layer_name)


def get_display_layers_for_transforms(transforms: Optional[list[str]] = None) -> list[str]:
    """
    Get a list of the display layers associated with a set of transforms
    :param transforms:
    :return:
    """
    nodes = transforms if transforms else get_selected_transforms()

    return cmds.listConnections(cmds.ls(nodes, tr=True)) if nodes else cmds.ls(type=ObjectType.displayLayer.name)


def get_display_layers(custom_only: bool = False):
    """
    Returns a list of all display layers
    :param custom_only:
    :return:
    """
    display_layers: list = cmds.ls(type=ObjectType.displayLayer.name)

    if custom_only:
        display_layers.remove(DEFAULT_LAYER)

    return display_layers


def remove_from_layer(objects: Sequence[str]):
    """
    Remove a list of objects to a layer
    :param objects:
    """
    cmds.editDisplayLayerMembers(DEFAULT_LAYER, objects)


def set_display_layer_color(display_layer: str, color: Point3):
    """
    Set the color of a display layer
    :param display_layer:
    :param color: color values in range 0 to 1
    """
    if is_display_layer(display_layer):
        cmds.setAttr(f'{display_layer}.color', True)
        cmds.setAttr(f'{display_layer}.overrideRGBColors', True)
        cmds.setAttr(f'{display_layer}.overrideColorRGB', *color.values)
    else:
        cmds.warning(f'Display layer not found: {display_layer}')


def is_display_layer(layer_name: str) -> bool:
    """
    Query if a display layer exists
    :param layer_name:
    :return:
    """
    return layer_name in get_display_layers()


def toggle_layer_shading(layer: str):
    """
    Toggle the shading for a specified layer
    :param layer:
    """
    if isinstance(layer, str):
        layer = cmds.ls(layer)

        if layer:
            layer = layer[0]

    if is_display_layer(layer_name=layer):
        cmds.setAttr(f'{layer}.shading', (1 - cmds.getAttr(f'{layer}.shading')))
    else:
        cmds.warning(f'Display layer not found: {layer}')


def toggle_current_layer_shading():
    """
    Toggle shading for layers representing the current object selection
    """
    for layer in get_selected_display_layers():
        toggle_layer_shading(layer=layer)


def list_layer_contents(layer_name: str) -> list[str] or None:
    """
    Get a list of objects in a display layer
    :param layer_name:
    :return:
    """
    if layer_name in get_display_layers_for_transforms():
        return cmds.editDisplayLayerMembers(layer_name, query=True)


def delete_empty_layers():
    """
    Purge empty display layers
    """
    for item in get_display_layers():
        if not list_layer_contents(item) and item != DEFAULT_LAYER:
            delete_display_layer(item)


def add_to_reference_layer(items: Sequence[str] = ()):
    """
    Add selected objects to a reference layer
    @param items:
    """
    items = cmds.ls(items, transforms=True) if items else cmds.ls(sl=True, transforms=True)

    if len(items) > 0:
        if REFERENCE_LAYER not in get_display_layers():
            reference_layer = create_display_layer(REFERENCE_LAYER)
            cmds.setAttr(reference_layer.shading, False)
            cmds.setAttr(reference_layer.displayType, 2)

        add_to_layer(items, REFERENCE_LAYER)


def get_selected_display_layers():
    layers = mel.eval('getLayerSelection("Display")')

    return [item for item in get_display_layers() if item in layers]


def get_layer_display_types(custom_only: bool = False) -> dict:
    """
    Gets a dict of layer names and their respective display types
    :return:
    """
    return {layer: LayerDisplayType.get_by_value(cmds.getAttr(f'{layer}.displayType'))
            for layer in get_display_layers(custom_only=custom_only)}


def set_layer_display_type(layer: str, layer_display_type: Union[int, LayerDisplayType]):
    """
    Set a layer display type
    :param layer:
    :param layer_display_type:
    """
    value = layer_display_type if type(layer) is int else layer_display_type.value
    cmds.setAttr(f'{layer}.displayType', value)
