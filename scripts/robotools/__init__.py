from __future__ import annotations

import contextlib

from enum import Enum, auto

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import attribute_utils, node_utils


class CustomAttribute(Enum):
    custom_type = auto()
    door_depth = auto()
    frame = auto()
    hinge_side = auto()
    opening_side = auto()
    pivot_anchor = auto()  # New: stores Anchor name (e.g., "c", "f0", "e5", "v3")
    pivot_side = auto()    # Legacy: stores Side name for old meshboxes
    sill_depth = auto()
    sill_thickness = auto()
    size = auto()
    skirt = auto()

    target_rise = auto()


class CustomType(Enum):
    boxy = auto()
    meshbox = auto()
    door = auto()
    staircase = auto()
    window = auto()


def is_boxy(node: str) -> bool:
    """Check if node is a boxy (boxyShape)."""
    from maya_tools.node_utils import get_shape_from_transform
    shape = get_shape_from_transform(node=node)
    return shape is not None and cmds.objectType(shape) == "boxyShape"


def is_custom_type(node: str, custom_type: CustomType) -> bool:
    """Is node a custom type (checks shape node first, then transform for legacy)."""
    from maya_tools.node_utils import get_shape_from_transform
    shape = get_shape_from_transform(node=node)
    # Check shape first (new standard)
    if shape and cmds.attributeQuery(CustomAttribute.custom_type.name, node=shape, exists=True):
        return cmds.getAttr(f"{shape}.{CustomAttribute.custom_type.name}") == custom_type.name
    return False


def is_custom_type_node(node: str) -> bool:
    """Is node a custom type node."""
    from maya_tools.node_utils import get_shape_from_transform
    shape = get_shape_from_transform(node=node)
    return shape and attribute_utils.has_attribute(node=shape, attr=CustomAttribute.custom_type.name)


def is_meshbox(node: str) -> bool:
    """Check if node is a Robotools meshbox by checking custom_type attribute.

    Args:
        node: Transform or shape node name.

    Returns:
        True if the node is a Robotools meshbox, False otherwise.
    """
    shape = node_utils.get_shape_from_transform(node=node)
    if not shape:
        return False
    if not cmds.attributeQuery(CustomAttribute.custom_type.name, node=shape, exists=True):
        return False
    return cmds.getAttr(f"{shape}.{CustomAttribute.custom_type.name}") == CustomType.meshbox.name
