from __future__ import annotations

from enum import Enum, unique, auto
from maya import cmds
from typing import Any, Optional, Sequence, Union

from core import color_classes
from core.core_enums import DataType


def add_attribute(node: str, attr: str, data_type: DataType, read_only: bool = False,
                  default_value: Optional[Any] = None) -> None:
    """
    Add an attribute to a DAG node
    :param node:
    :param attr:
    :param data_type:
    :param read_only:
    :param default_value:
    """
    if data_type in (DataType.float, DataType.double):
        cmds.addAttr(node, longName=attr, attributeType=data_type.name)
    else:
        cmds.addAttr(node, longName=attr, dataType=data_type.name)
    if default_value is not None:
        set_attribute(node=node, attr=attr, value=default_value)
    if read_only:
        cmds.setAttr(f"{node}.{attr}", lock=True)


def add_color_attribute(node: str, attr: str, read_only: bool = False,
                        default_value: color_classes.RGBColor = color_classes.MAGENTA) -> None:
    """
    Add a color attribute to a DAG node
    :param default_value:
    :param node:
    :param attr:
    :param read_only:
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
    if read_only:
        cmds.setAttr(f"{node}.{attr}", lock=True)


def add_compound_attribute(node: str, parent_attr: str, data_type: DataType, attrs: list[str],
                           default_values: Optional[Any] = None, read_only: bool = False) -> None:
    """
    Add a compound attribute to a DAG node
    :param read_only:
    :param default_values:
    :param node:
    :param parent_attr:
    :param data_type:
    :param attrs:
    """
    child_data_type: DataType = {
        DataType.double2: DataType.double,
        DataType.double3: DataType.double,
        DataType.float2: DataType.float,
        DataType.float3: DataType.float,
        DataType.int2: DataType.int,
        DataType.int3: DataType.int,
    }.get(data_type)
    assert data_type is not None, f'Data type not supported: {data_type}'
    cmds.addAttr(node, longName=parent_attr, attributeType=data_type.name)
    for attr in attrs:
        cmds.addAttr(node, longName=attr, attributeType=child_data_type.name, parent=parent_attr)
    if default_values is not None:
        set_attribute(node=node, attr=parent_attr, value=default_values)
    if read_only:
        cmds.setAttr(f"{node}.{parent_attr}", lock=True)


def add_enum_attribute(node: str, attr: str, values: list[str], default_index: int = 0) -> None:
    """
    Add an attribute to a DAG node.
    :param node:
    :param attr:
    :param values:
    :param default_index:
    """
    cmds.addAttr(node, longName=attr, attributeType=DataType.enum.name, enumName=":".join(values), keyable=True)
    cmds.setAttr(f"{node}.{attr}", default_index)


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
    if attr_data in (DataType.float3, DataType.double3, DataType.float2, DataType.double2):
        cmds.setAttr(f'{node}.{attr}', *value, type=attr_data.name, lock=lock)
    elif attr_data in (DataType.string, DataType.message):
        cmds.setAttr(f'{node}.{attr}', value, type=attr_data.name, lock=lock)
    else:
        cmds.setAttr(f'{node}.{attr}', value, lock=lock)


if __name__ == '__main__':
    test_node = createGroupNode(name='testNode', overwrite=True)
    addAttribute(transform=test_node, attr_name='metadata', data_type=DataType.string)
