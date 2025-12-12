from maya import cmds
from typing import Any, Optional, Sequence, Union
from enum import Enum, unique, auto
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


def add_compound_attribute(node: str, parent_attr: str, data_type: DataType, attrs: list[str]):
    """
    Add a compound attribute to a DAG node
    :param node:
    :param parent_attr:
    :param data_type:
    :param attrs:
    """
    child_data_type: DataType = {
        DataType.double2: DataType.double,
        DataType.double3: DataType.double,
        DataType.float2: DataType.float,
        DataType.float3: DataType.float
    }.get(data_type)
    assert data_type is not None, f'Data type not supported: {data_type}'
    cmds.addAttr(node, longName=parent_attr, attributeType=data_type.name)
    for attr in attrs:
        cmds.addAttr(node, longName=attr, attributeType=child_data_type.name, parent=parent_attr)


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


def delete_attribute(transform: str, attr: str):
    """
    Delete an attribute
    :param transform:
    :param attr:
    """
    cmds.setAttr(f'{transform}.{attr}', lock=False)
    cmds.deleteAttr(f'{transform}.{attr}')


if __name__ == '__main__':
    test_node = createGroupNode(name='testNode', overwrite=True)
    addAttribute(transform=test_node, attr_name='metadata', data_type=DataType.string)
