from __future__ import annotations

from enum import Enum, unique, auto
from maya import cmds
from typing import Any, Optional, Sequence, Union

from core import color_classes
from core.core_enums import DataType


def add_attribute(node: str, attr: str, data_type: DataType,
                  channel_box: bool = False, lock: bool = False,
                  default_value: Optional[Any] = None) -> None:
    """
    Add an attribute to a DAG node
    :param node:
    :param attr:
    :param data_type:
    :param lock:
    :param channel_box:
    :param default_value:
    """
    # Types that use attributeType (numeric types)
    attribute_types = {'float', 'double', 'bool', 'long', 'short', 'byte', 'char', 'enum', 'int',
                       'float2', 'float3', 'double2', 'double3', 'long2', 'long3', 'short2', 'short3',
                       'int2', 'int3'}
    type_name = data_type.name
    # Map Python/DataType names to Maya's preferred attribute types
    type_mapping = {'float': 'double', 'int': 'long', 'int2': 'long2', 'int3': 'long3'}
    maya_type_name = type_mapping.get(type_name, type_name)
    if type_name in attribute_types:
        cmds.addAttr(node, longName=attr, attributeType=maya_type_name)
    else:
        cmds.addAttr(node, longName=attr, dataType=type_name)
    if default_value is not None:
        set_attribute(node=node, attr=attr, value=default_value)
    cmds.setAttr(f"{node}.{attr}", lock=lock, channelBox=channel_box)


def add_color_attribute(node: str, attr: str, channel_box: bool = False, lock: bool = False,
                        default_value: color_classes.ColorRGB = color_classes.MAGENTA) -> None:
    """
    Add a color attribute to a DAG node
    :param default_value:
    :param node:
    :param attr:
    :param channel_box:
    :param lock:
    :return:
    """
    cmds.addAttr(
        node,
        longName=attr,
        attributeType=DataType.float3.name,
        usedAsColor=True
    )
    cmds.addAttr(
        node,
        longName="red",
        parent=attr,
        attributeType=DataType.float.name,
    )
    cmds.addAttr(
        node,
        longName="green",
        parent=attr,
        attributeType=DataType.float.name,
    )
    cmds.addAttr(
        node,
        longName="blue",
        parent=attr,
        attributeType=DataType.float.name,
    )
    if default_value is not None:
        set_attribute(node=node, attr=attr, value=default_value.normalized)
    cmds.setAttr(f"{node}.{attr}", lock=lock, channelBox=channel_box)


def add_compound_attribute(node: str, parent_attr: str, data_type: DataType, attrs: list[str],
                           default_values: Optional[Any] = None, channel_box: bool = False, lock: bool = False) -> None:
    """
    Add a compound attribute to a DAG node
    :param default_values:
    :param node:
    :param parent_attr:
    :param data_type:
    :param attrs:
    :param channel_box:
    :param lock:
    """
    # Use string keys to avoid module reload issues with enum identity
    child_data_type_map = {
        DataType.double2.name: DataType.double,
        DataType.double3.name: DataType.double,
        DataType.float2.name: DataType.float,
        DataType.float3.name: DataType.float,
        DataType.int2.name: DataType.int,
        DataType.int3.name: DataType.int,
    }
    child_data_type: DataType = child_data_type_map.get(data_type.name)
    assert child_data_type is not None, f'Data type not supported: {data_type}'
    cmds.addAttr(node, longName=parent_attr, attributeType=data_type.name)
    for attr in attrs:
        cmds.addAttr(node, longName=attr, attributeType=child_data_type.name, parent=parent_attr)
    if default_values is not None:
        set_attribute(node=node, attr=parent_attr, value=default_values)
    cmds.setAttr(f"{node}.{parent_attr}", channelBox=channel_box, lock=lock)


def add_enum_attribute(node: str, attr: str, values: list[str], default_index: int = 0,
                       channel_box: bool = False, lock: bool = False) -> None:
    """
    Add an attribute to a DAG node.
    :param node:
    :param attr:
    :param values:
    :param channel_box:
    :param lock:
    :param default_index:
    """
    cmds.addAttr(node, longName=attr, attributeType=DataType.enum.name, enumName=":".join(values), keyable=True)
    cmds.setAttr(f"{node}.{attr}", default_index)
    cmds.setAttr(f"{node}.{attr}", channelBox=channel_box, lock=lock)


def delete_attribute(transform: str, attr: str):
    """
    Delete an attribute
    :param transform:
    :param attr:
    """
    cmds.setAttr(f'{transform}.{attr}', lock=False)
    cmds.deleteAttr(f'{transform}.{attr}')


def has_attribute(node: str, attr: str) -> bool:
    """Queries if a node has an attribute."""
    return cmds.attributeQuery(attr, node=node, exists=1)


def get_attribute(node: str, attr: str) -> Any | False:
    """Query the value of an attribute.

    :param node:
    :param attr:
    :return: value or None
    """
    return cmds.getAttr(f"{node}.{attr}") if has_attribute(node=node, attr=attr) else None


def set_attribute(node: str, attr: str, value: Union[int, float, str, Sequence], lock: bool = False):
    """
    Set an attribute
    :param node:
    :param attr:
    :param value:
    :param lock:
    """
    attr_type = cmds.getAttr(f'{node}.{attr}', type=True)
    attr_data = DataType[attr_type]
    # Use string comparison to avoid module reload issues with enum identity
    if attr_data.name in ('float3', 'double3', 'float2', 'double2'):
        cmds.setAttr(f'{node}.{attr}', *value, type=attr_data.name, lock=lock)
    elif attr_data.name in ('string', 'message'):
        cmds.setAttr(f'{node}.{attr}', value, type=attr_data.name, lock=lock)
    else:
        cmds.setAttr(f'{node}.{attr}', value, lock=lock)


def set_lock(node: str, attr: str, lock_state: bool = True):
    """Set the lock state of an attribute.

    Args:
        node: The node name.
        attr: The attribute name.
        lock_state: True to lock, False to unlock.
    """
    cmds.setAttr(f'{node}.{attr}', lock=lock_state)


if __name__ == '__main__':
    test_node = createGroupNode(name='testNode', overwrite=True)
    addAttribute(transform=test_node, attr_name='metadata', data_type=DataType.string)
