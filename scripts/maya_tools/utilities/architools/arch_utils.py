from __future__ import annotations

import logging

from maya import cmds

from core import color_classes
from core.core_enums import CustomType, Side
from core.logging_utils import get_logger
from core.point_classes import Point3
from maya_tools import node_utils
from maya_tools.utilities.boxy import boxy


LOGGER = get_logger(name=__name__, level=logging.INFO)


def convert_node_to_boxy(node: str, delete: bool = False) -> any:
    """Convert a geometry node to a boxy node."""
    try:
        data = boxy.BoxyData(
            position=node_utils.get_translation(node=node),
            rotation=node_utils.get_rotation(node=node),
            size=Point3(*cmds.getAttr(f"{node}.size")[0]),
            pivot=Side.bottom,
            color=color_classes.DEEP_GREEN,
            name="boxy"
        )
        if delete:
            cmds.delete(node)
        return boxy.build(boxy_data=data)
    except Exception as e:
        LOGGER.info(f"Could not create boxy for {node}: {e}")
        return False


def get_custom_type(custom_type: CustomType, selected: bool = False) -> list[str]:
    """Get a list of custom type nodes."""
    search_list = node_utils.get_selected_transforms() if selected else node_utils.get_transforms()
    return [x for x in search_list if node_utils.is_custom_type(node=x, custom_type=custom_type)]
