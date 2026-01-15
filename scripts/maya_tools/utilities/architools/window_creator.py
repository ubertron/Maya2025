"""Window Creator."""
from __future__ import annotations

import logging
import math

from maya import cmds

from core import color_classes
from core.core_enums import CustomType, DataType
from core.logging_utils import get_logger
from core.point_classes import Point3
from maya_tools import attribute_utils, material_utils, node_utils
from maya_tools.geometry import geometry_utils, curve_utils
from maya_tools.utilities.architools import CURVE_COLOR
from maya_tools.utilities.architools.arch_creator import ArchCreator
from maya_tools.utilities.architools.data.window_data import WindowData

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class WindowCreator(ArchCreator):
    def __init__(self, sill_thickness: float, sill_depth: float, frame: float, skirt: float,
                 auto_texture: bool):
        super().__init__(custom_type=CustomType.window, auto_texture=auto_texture)

        # initialize bespoke properties
        self.sill_thickness = sill_thickness
        self.sill_depth = sill_depth
        self.frame = frame
        self.skirt = skirt


    def initialize_arch_data(self):
        """Initialize the data from selected boxy."""
        self.data = WindowData(
            translation=self.translation,
            y_rotation=self.rotation.y,
            size=self.size,
            sill_thickness=self.sill_thickness,
            sill_depth=self.sill_depth,
            frame=self.frame,
            skirt=self.skirt,
        )

    def create(self):
        """Create the window geometry."""
        # 1) initialize arch data
        self.initialize_arch_data()

        # 2)  curves from the arch data
        for x in self.data.window_frame_profile_points:
            LOGGER.debug(x)

        curves = [curve_utils.create_curve_from_points(
            points=self.data.window_frame_profile_points, close=False, name=f"{self.custom_type.name}_curve0",
            color=CURVE_COLOR)]

        # node_utils.set_translation(nodes=curves[0], value=self.data.window_frame_profile_positions[0], absolute=True)
        node_utils.set_pivot(nodes=curves[0], value=self.data.window_frame_profile_positions[0])

        for i in range(1, 4):
            curves.append(node_utils.duplicate(node=curves[0], name=f"{self.custom_type.name}_curve{i}"))
            node_utils.set_translation(nodes=curves[i], value=self.data.window_frame_profile_positions[i], absolute=True)
            node_utils.set_rotation(nodes=curves[i], value=Point3(0, 0, self.data.window_frame_profile_rotations[i]))
            if 0 < i < 3:
                cmds.setAttr(f"{curves[i]}.scaleX", math.sqrt(2))

        cmds.move(self.sill_thickness, curves[0], curves[-1], moveY=True, relative=True, worldSpace=True)

        # 3) create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        window_frame, loft = cmds.loft(*curves, degree=1, polygon=1, name="window_frame")
        window_sill, poly_cube_node = cmds.polyCube(width=self.data.sill_size.x, height=self.data.sill_size.y, depth=self.data.sill_size.z, name="window_sill")
        cmds.setAttr(f"{poly_cube_node}.heightBaseline", -1)
        geometry = geometry_utils.combine(transforms=[window_frame, window_sill], name=self.custom_type.name)

        # 4) add the attributes
        attribute_utils.add_attribute(
            node=geometry, attr="custom_type", data_type=DataType.string, lock=True,
            default_value=self.custom_type.name)
        attribute_utils.add_compound_attribute(
            node=geometry, parent_attr="size", data_type=DataType.float3, attrs=["x", "y", "z"],
            lock=True, default_values=self.data.size.values)
        attribute_utils.add_attribute(
            node=geometry, attr="frame", data_type=DataType.float, lock=True, default_value=self.frame)
        attribute_utils.add_attribute(
            node=geometry, attr="skirt", data_type=DataType.float, lock=True, default_value=self.skirt)
        attribute_utils.add_attribute(
            node=geometry, attr="sill_thickness", data_type=DataType.float, lock=True, default_value=self.sill_thickness)
        attribute_utils.add_attribute(
            node=geometry, attr="sill_depth", data_type=DataType.float, lock=True, default_value=self.sill_depth)

        # 5) texture/wireframe color
        geometry_utils.set_wireframe_color(node=geometry, color=color_classes.DEEP_GREEN)
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


if __name__ == "__main__":
    window_creator = WindowCreator()
    print(window_creator.data)