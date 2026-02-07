"""Door Creator"""
from __future__ import annotations

import logging
import math

from maya import cmds

from core import color_classes
from core.core_enums import CustomType, DataType, Side
from core.logging_utils import get_logger
from core.point_classes import Point3
from maya_tools import attribute_utils, material_utils, node_utils
from maya_tools.geometry import geometry_utils, curve_utils
from maya_tools.utilities.architools import CURVE_COLOR
from maya_tools.utilities.architools.arch_creator import ArchCreator
from maya_tools.utilities.architools.data.door_data import DoorData

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class DoorCreator(ArchCreator):
    def __init__(self, frame: float, skirt: float, door_depth: float, hinge_side: Side, opening_side: Side,
                 auto_texture: bool):
        super().__init__(custom_type=CustomType.door, auto_texture=auto_texture)

        # initialize bespoke properties
        assert hinge_side in (Side.left, Side.right), "Invalid hinge side"
        assert opening_side in (Side.front, Side.back), "Invalid opening side"
        self.frame = frame
        self.skirt = skirt
        self.door_depth = door_depth
        self.hinge_side = hinge_side
        self.opening_side = opening_side
        LOGGER.debug(f"frame: {frame}, skirt: {skirt}, door_depth: {door_depth}, hinge_side: {hinge_side}")

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
        curves = [curve_utils.create_curve_from_points(
            points=self.data.doorway_profile_points, close=False, name=f"{self.custom_type.name}_curve0", color=CURVE_COLOR)]
        print(self.data.doorway_profile_points)
        node_utils.set_pivot(nodes=curves[0], value=self.data.doorway_profile_positions[0])

        for i in range(1, 4):
            curves.append(node_utils.duplicate(node=curves[0], name=f"{self.custom_type.name}_curve{i}"))
            node_utils.set_translation(nodes=curves[i], value=self.data.doorway_profile_positions[i])
            node_utils.set_rotation(nodes=curves[i], value=Point3(0, 0, self.data.doorway_profile_rotations[i]))
            if 0 < i < 3:
                cmds.setAttr(f"{curves[i]}.scaleX", math.sqrt(2))

        # 3) create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        geometry, loft = cmds.loft(*curves, degree=1, polygon=1, name="door_frame")

        # 4) add the attributes (custom_type on shape node for consistency)
        shape = node_utils.get_shape_from_transform(geometry)
        attribute_utils.add_attribute(
            node=shape, attr="custom_type", data_type=DataType.string, lock=True,
            default_value=self.custom_type.name)
        attribute_utils.add_compound_attribute(
            node=geometry, parent_attr="size", data_type=DataType.float3, attrs=["x", "y", "z"],
            lock=True, default_values=self.data.size.values)
        attribute_utils.add_attribute(
            node=geometry, attr="frame", data_type=DataType.float, lock=True, default_value=self.frame)
        attribute_utils.add_attribute(
            node=geometry, attr="skirt", data_type=DataType.float, lock=True, default_value=self.skirt)
        attribute_utils.add_attribute(
            node=geometry, attr="door_depth", data_type=DataType.float, lock=True, default_value=self.door_depth)
        attribute_utils.add_attribute(
            node=geometry, attr="hinge_side", data_type=DataType.string, lock=True,
            default_value=self.hinge_side.name)
        attribute_utils.add_attribute(
            node=geometry, attr="opening_side", data_type=DataType.string, lock=True,
            default_value=self.opening_side.name)

        # 5) texture/wireframe color
        geometry_utils.set_wireframe_color(node=geometry, color=self.color)
        if self.auto_texture:
            material_utils.auto_texture(transform=geometry)

        # 6) cleanup
        cmds.polySoftEdge(geometry, angle=0)
        node_utils.pivot_to_base(node=geometry)
        cmds.delete(geometry, constructionHistory=True)
        cmds.delete(curves, self.boxy_node)
        node_utils.set_translation(geometry, value=self.data.translation)
        node_utils.set_rotation(geometry, value=Point3(0, self.data.y_rotation, 0))
        cmds.select(clear=True)
        cmds.select(geometry)
        return geometry
