# Staircase Creator
from __future__ import annotations

import contextlib
import logging

from core import color_classes, math_utils
from core.core_enums import Axis, DataType, CustomType
from core.logging_utils import get_logger
from core.point_classes import Point3, Y_AXIS

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils, attribute_utils, geometry_utils, material_utils, curve_utils
    from maya_tools.utilities.architools import CURVE_COLOR
    from maya_tools.utilities.architools.arch_creator import ArchCreator
    from maya_tools.utilities.architools.data.staircase_data import StaircaseData

LOGGER = get_logger(__name__, level=logging.INFO)


class StaircaseCreator(ArchCreator):
    def __init__(self, target_rise: float = 20.0, auto_texture: bool = False):
        super().__init__(custom_type=CustomType.staircase, auto_texture=auto_texture)

        # initialize bespoke properties
        self.target_rise = target_rise

    def initialize_arch_data(self):
        """Initialize the data from the boxy node."""

        # evaluate count based on default tread
        count = round(self.size.y / self.target_rise)
        LOGGER.debug(self.size.y, count)

        self.data = StaircaseData(
            translation=self.translation,
            y_rotation=self.rotation.y,
            size=self.size,
            count=count,
        )

    @property
    def data(self) -> StaircaseData | None:
        return self._data

    @data.setter
    def data(self, value: StaircaseData):
        self._data = value

    def create(self):
        """Create the staircase geometry."""
        # 1) initialize arch data
        self.initialize_arch_data()

        # 2) create curves from the arch data
        curve0 = curve_utils.create_curve_from_points(
            self.data.profile_points, close=False, name=f"{self.custom_type.name}_curve0", color=CURVE_COLOR)
        cmds.setAttr(f"{curve0}.translateX", -self.data.size.x / 2)
        curve1 = cmds.duplicate(curve0, name=f"{self.custom_type.name}_curve1")[0]
        cmds.setAttr(f"{curve1}.translateX", self.data.size.x / 2)
        curves = [curve0, curve1]

        # 3) create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        geometry, loft = cmds.loft(*curves, degree=1, polygon=1, name=self.custom_type.name)

        # reverse the staircase normals if the stairs are inside out
        tread_normal = geometry_utils.get_face_normal(node=geometry, face_id=1)
        dot_product = math_utils.dot_product(vector_a=tread_normal, vector_b=Y_AXIS, normalize=True)
        if dot_product < 0.0:
            cmds.polyNormal(geometry, normalMode=0, userNormalMode=0)

        # 4) add the attributes
        attribute_utils.add_attribute(
            node=geometry, attr="custom_type", data_type=DataType.string, lock=True,
            default_value=self.custom_type.name)
        attribute_utils.add_compound_attribute(
            node=geometry, parent_attr="size", data_type=DataType.float3, attrs=["x", "y", "z"], lock=True,
            default_values=self.data.size.values)
        attribute_utils.add_attribute(
            node=geometry, attr="target_rise", data_type=DataType.float, lock=True, default_value=self.target_rise)

        # 5) texture/wireframe color
        geometry_utils.set_wireframe_color(node=geometry, color=color_classes.DEEP_GREEN)
        if self.auto_texture:
            material_utils.auto_texture(transform=geometry)

        # 6) cleanup
        cmds.polySoftEdge(geometry, angle=0)
        cmds.delete(geometry, constructionHistory=True)
        cmds.delete(curves, self.boxy_node)
        node_utils.set_translation(geometry, value=self.data.translation)
        node_utils.set_rotation(geometry, value=Point3(0, self.data.y_rotation, 0))
        cmds.select(clear=True)
        cmds.select(geometry)
        return geometry


if __name__ == "__main__":
    if cmds.ls("spline_*"):
        cmds.delete("spline_*")
    if cmds.ls("staircase*"):
        cmds.delete("staircase*")
    cmds.select("locator*")
    stairs = StaircaseCreator(axis=Axis.z)
    print(stairs.data)
    stairs.create()