"""Door Creator"""
from __future__ import annotations

import logging

import math
from maya import cmds

from core import math_utils
from core.core_enums import Side, Axis, DataType
from core.logging_utils import get_logger
from core.point_classes import Point3, Point3Pair, X_AXIS, Z_AXIS
from maya_tools import attribute_utils, curve_utils, material_utils, node_utils
from maya_tools.utilities.architools import CURVE_COLOR
from maya_tools.utilities.architools.arch_creator import ArchCreator
from maya_tools.utilities.architools.door_data import DoorData

LOGGER = get_logger(name=__name__, level=logging.INFO)


class DoorCreator(ArchCreator):
    def __init__(self, frame: float = 10.0, skirt: float = 2.0, door_depth: float = 5.0,
                 hinge_side: Side = Side.left, opening_side: Side = Side.front, rotation: float | None = None):
        super().__init__()
        assert hinge_side in (Side.left, Side.right), "Invalid hinge side"
        assert opening_side in (Side.front, Side.back), "Invalid opening side"
        self.frame = frame
        self.skirt = skirt
        self.door_depth = door_depth
        self.hinge_side = hinge_side
        self.opening_side = opening_side
        self.rotation = rotation
        self.positions = None
        LOGGER.debug(self.data)

    def __repr__(self):
        print(self.door_depth)

    def validate(self):
        """Initialize the data from selected items."""
        self.positions = node_utils.get_points_from_selection()
        assert len(self.positions) == 2, "Select two vertices or locators"
        minimum_point = Point3(*[min(x.values[i] for x in self.positions) for i in range(3)])
        maximum_point = Point3(*[max(x.values[i] for x in self.positions) for i in range(3)])
        spatial_bounds = Point3Pair(a=minimum_point, b=maximum_point)

        # get rotation (if rotation supplied, use that)
        if hasattr(self, "rotation") and self.rotation:
            rotation = self.rotation
        else:
            # otherwise, use the cavity_bounds to work out if the axis is x or z
            rotation = 0.0 if Point3Pair(spatial_bounds.min_max_vector, X_AXIS).dot_product > \
                              Point3Pair(spatial_bounds.min_max_vector, Z_AXIS).dot_product else 90.0

        # TODO: add algorithm that derives the exact rotation from surrounding geometry

        # get the size based on the rotation (to align with the X/Z axes)
        size = math_utils.calculate_size_with_y_offset(points=Point3Pair(*self.positions), y_offset=-rotation)
        print(f"Size: {size}")
        print(f"Rotation: {rotation}")

        # validate minimum bounds for locators

        self.data = DoorData(
            position=spatial_bounds.base_center,
            rotation=rotation,
            size=size,
            door_depth=self.door_depth,
            hinge_side=self.hinge_side,
            opening_side=self.opening_side,
            frame=self.frame,
            skirt=self.skirt
        )

    def create(self, auto_texture: bool = False) -> str:
        """Create the door geometry."""
        # create the door curves
        for x in self.data.doorway_profile_points:
            LOGGER.debug(x)
        door_curves = [curve_utils.create_curve_from_points(points=self.data.doorway_profile_points, close=False,
                                                            name="door_curve0", color=CURVE_COLOR)]
        node_utils.set_pivot(nodes=door_curves[0], value=self.data.doorway_profile_positions[0])

        for i in range(1, 4):
            door_curves.append(node_utils.duplicate(node=door_curves[0], name=f"door_curve{i}"))
            node_utils.set_translation(nodes=door_curves[i], value=self.data.doorway_profile_positions[i])
            node_utils.set_rotation(nodes=door_curves[i], value=Point3(0, 0, self.data.doorway_profile_rotations[i]))
            if 0 < i < 3:
                cmds.setAttr(f"{door_curves[i]}.scaleX", math.sqrt(2))

        # create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        door_frame, loft = cmds.loft(*door_curves, degree=1, polygon=1, name="door_frame")

        # attributes
        attribute_utils.add_attribute(
            node=door_frame, attr="custom_type", data_type=DataType.string, read_only=True, default_value="door")
        attribute_utils.add_compound_attribute(
            node=door_frame, parent_attr="size", data_type=DataType.float3, attrs=["x", "y", "z"],
            read_only=True, default_values=self.data.size.values)
        attribute_utils.add_attribute(
            node=door_frame, attr="frame", data_type=DataType.float, read_only=True, default_value=self.frame)
        attribute_utils.add_attribute(
            node=door_frame, attr="skirt", data_type=DataType.float, read_only=True, default_value=self.skirt)
        attribute_utils.add_attribute(
            node=door_frame, attr="door_depth", data_type=DataType.float, read_only=True, default_value=self.door_depth)
        attribute_utils.add_attribute(
            node=door_frame, attr="hinge_side", data_type=DataType.string, read_only=True,
            default_value=self.hinge_side.name)
        attribute_utils.add_attribute(
            node=door_frame, attr="opening_side", data_type=DataType.string, read_only=True,
            default_value=self.opening_side.name)

        # texture
        if auto_texture:
            material_utils.auto_texture(transform=door_frame)

        # cleanup
        cmds.polySoftEdge(door_frame, angle=0)
        node_utils.pivot_to_base(node=door_frame)
        cmds.delete(door_frame, constructionHistory=True)
        cmds.delete(door_curves)
        node_utils.set_translation(door_frame, value=self.data.position)
        node_utils.set_rotation(door_frame, value=Point3(0, self.data.rotation, 0))
        cmds.select(clear=True)
        cmds.select(door_frame)
        return door_frame
