from maya import cmds
from typing import Any, Optional, Sequence, Union
from enum import Enum, unique, auto


@unique
class DataType(Enum):
    char = auto()
    double = auto()
    double2 = auto()
    double3 = auto()
    float = auto()
    float2 = auto()
    float3 = auto()
    message = auto()
    string = auto()

    @staticmethod
    def get_by_key(key: str) -> Enum or None:
        return DataType.__members__.get(key)


def add_attribute(transform: str, attr: str, data_type: DataType):
    """
    Add an attribute to a DAG node
    :param transform:
    :param attr:
    :param data_type:
    """
    if data_type in (DataType.float, DataType.double):
        cmds.addAttr(transform, longName=attr, attributeType=data_type.name)
    else:
        cmds.addAttr(transform, longName=attr, dataType=data_type.name)


def add_compound_attribute(transform: str, parent_attr: str, data_type: DataType, attrs: list[str]):
    """
    Add a compound attribute to a DAG node
    :param transform:
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
    cmds.addAttr(transform, longName=parent_attr, attributeType=data_type.name)

    for attr in attrs:
        cmds.addAttr(transform, longName=attr, attributeType=child_data_type.name, parent=parent_attr)


def set_attribute(transform: str, attr: str, value: Union[int, float, str, Sequence], lock: bool = False):
    """
    Set an attribute
    :param transform:
    :param attr:
    :param value:
    :param lock:
    """
    attr_type = cmds.getAttr(f'{transform}.{attr}', type=True)
    attr_data = DataType.get_by_key(attr_type)

    if attr_data in (DataType.float3, DataType.double3, DataType.float2, DataType.double2):
        cmds.setAttr(f'{transform}.{attr}', *value, type=attr_data.name, lock=lock)
    elif attr_data in (DataType.string, DataType.message):
        cmds.setAttr(f'{transform}.{attr}', value, type=attr_data.name, lock=lock)
    else:
        cmds.setAttr(f'{transform}.{attr}', value, lock=lock)


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
