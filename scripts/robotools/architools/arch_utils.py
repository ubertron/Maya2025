from __future__ import annotations

import contextlib
import logging

import robotools
from core.core_enums import Side
from robotools import CustomType
from core.logging_utils import get_logger
from core.point_classes import Point3
from robotools.architools import ARCHITOOLS_COLOR
from robotools.boxy import boxy_utils
from robotools.boxy.boxy_data import BoxyData
from core.bounds import Bounds

with contextlib.suppress(ImportError):
    from maya_tools import node_utils
    from maya import cmds

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


def convert_node_to_boxy(node: str, delete: bool = False) -> any:
    """Convert a geometry node to a boxy node."""
    try:
        # Calculate the bounds from the object data as the actual size is bigger than the reference size
        # TODO: position issue band-aid - remove when fixed
        position = node_utils.get_translation(node, absolute=True)
        bounds = Bounds(
            size=Point3(*cmds.getAttr(f"{node}.size")[0]),
            position=position,
            rotation=node_utils.get_rotation(node=node)
        )
        data = BoxyData(
            size=bounds.size,
            translation=position,
            rotation=node_utils.get_rotation(node=node),
            pivot_side=Side.bottom,
            color=ARCHITOOLS_COLOR
        )
        LOGGER.debug(f">>> convert_node_to_boxy - data: {data}")
        if delete:
            cmds.delete(node)
        result = boxy_utils.build(boxy_data=data)

        # TODO: position issue band-aid - remove when fixed
        node_utils.set_translation(nodes=result, value=position)
        return result
    except Exception as e:
        LOGGER.info(f"Could not create boxy for {node}: {e}")
        return False


def get_custom_type(custom_type: CustomType, selected: bool = False) -> list[str]:
    """Get a list of custom type nodes."""
    search_list = node_utils.get_selected_transforms() if selected else node_utils.get_transforms()
    return [x for x in search_list if robotools.is_custom_type(node=x, custom_type=custom_type)]
