"""Door Creator"""
from __future__ import annotations

import logging

import math
from maya import cmds

from core import color_classes, math_utils
from core.core_enums import Side, Axis, DataType
from core.logging_utils import get_logger
from core.point_classes import Point3, Point3Pair, X_AXIS, Z_AXIS
from maya_tools import attribute_utils, curve_utils, material_utils, node_utils
from maya_tools.utilities.architools import CURVE_COLOR
from maya_tools.utilities.architools.arch_creator import ArchCreator
from maya_tools.utilities.architools.door_data import DoorData
from maya_tools.utilities.boxy import boxy

LOGGER = get_logger(name=__name__, level=logging.INFO)


class DoorCreator(ArchCreator):
    def __init__(self, frame: float = 10.0, skirt: float = 2.0, door_depth: float = 5.0,
                 hinge_side: Side = Side.left, opening_side: Side = Side.front,
                 auto_texture: bool = False):
        super().__init__(auto_texture=auto_texture)

        # initialize bespoke properties
        assert hinge_side in (Side.left, Side.right), "Invalid hinge side"
        assert opening_side in (Side.front, Side.back), "Invalid opening side"
        self.frame = frame
        self.skirt = skirt
        self.door_depth = door_depth
        self.hinge_side = hinge_side
        self.opening_side = opening_side

    def __repr__(self):
        return self.door_depth

    def initialize_arch_data(self):
        """Initialize the data from selected boxy."""
        self.data = DoorData(
            translation=self.translation,
            y_rotation=self.rotation.y,
            size=self.size,
            door_depth=self.door_depth,
            hinge_side=self.hinge_side,
            opening_side=self.opening_side,
            frame=self.frame,
            skirt=self.skirt
        )

    def create(self) -> str:
        """Create the door geometry."""
        # 1) initialize arch data
        self.initialize_arch_data()

        # 2)  curves from the arch data
        for x in self.data.doorway_profile_points:
            LOGGER.debug(x)
        doorway_curves = [curve_utils.create_curve_from_points(points=self.data.doorway_profile_points, close=False,
                                                            name="door_curve0", color=CURVE_COLOR)]
        node_utils.set_pivot(nodes=doorway_curves[0], value=self.data.doorway_profile_positions[0])

        for i in range(1, 4):
            doorway_curves.append(node_utils.duplicate(node=doorway_curves[0], name=f"door_curve{i}"))
            node_utils.set_translation(nodes=doorway_curves[i], value=self.data.doorway_profile_positions[i])
            node_utils.set_rotation(nodes=doorway_curves[i], value=Point3(0, 0, self.data.doorway_profile_rotations[i]))
            if 0 < i < 3:
                cmds.setAttr(f"{doorway_curves[i]}.scaleX", math.sqrt(2))

        # 3) create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        door_frame, loft = cmds.loft(*doorway_curves, degree=1, polygon=1, name="door_frame")

        # 4) add the attributes
        attribute_utils.add_attribute(
            node=door_frame, attr="custom_type", data_type=DataType.string, lock=True, default_value="door")
        attribute_utils.add_compound_attribute(
            node=door_frame, parent_attr="size", data_type=DataType.float3, attrs=["x", "y", "z"],
            lock=True, default_values=self.data.size.values)
        attribute_utils.add_attribute(
            node=door_frame, attr="frame", data_type=DataType.float, lock=True, default_value=self.frame)
        attribute_utils.add_attribute(
            node=door_frame, attr="skirt", data_type=DataType.float, lock=True, default_value=self.skirt)
        attribute_utils.add_attribute(
            node=door_frame, attr="door_depth", data_type=DataType.float, lock=True, default_value=self.door_depth)
        attribute_utils.add_attribute(
            node=door_frame, attr="hinge_side", data_type=DataType.string, lock=True,
            default_value=self.hinge_side.name)
        attribute_utils.add_attribute(
            node=door_frame, attr="opening_side", data_type=DataType.string, lock=True,
            default_value=self.opening_side.name)

        # 5) texture
        if self.auto_texture:
            material_utils.auto_texture(transform=door_frame)

        # 6) cleanup
        cmds.polySoftEdge(door_frame, angle=0)
        node_utils.pivot_to_base(node=door_frame)
        cmds.delete(door_frame, constructionHistory=True)
        cmds.delete(doorway_curves, self.boxy_node)
        node_utils.set_translation(door_frame, value=self.data.translation)
        node_utils.set_rotation(door_frame, value=Point3(0, self.data.y_rotation, 0))
        cmds.select(clear=True)
        cmds.select(door_frame)
        return door_frame


def convert_door_to_boxy(door: str, delete: bool = False) -> any:
    """Convert a door object to a boxy node."""
    try:
        data = boxy.BoxyData(
            position=node_utils.get_translation(node=door),
            rotation=node_utils.get_rotation(node=door),
            size=Point3(*cmds.getAttr(f"{door}.size")[0]),
            pivot=Side.bottom,
            color=color_classes.DEEP_GREEN,
            name="boxy"
        )
        if delete:
            cmds.delete(door)
        return boxy.build(boxy_data=data)
    except Exception as e:
        LOGGER.info(f"Could not create boxy for door {door}: {e}")
        return False


def get_selected_doors() -> list[str]:
    """Get a list of all selected doors."""
    return [x for x in node_utils.get_selected_transforms(full_path=True) if  node_utils.is_door(x)]
