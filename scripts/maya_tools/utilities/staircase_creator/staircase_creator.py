# Staircase Creator
from __future__ import annotations

import contextlib
import logging
import math

from dataclasses import dataclass

from core import math_funcs
from core.core_enums import Axis, DataType
from core.logging_utils import get_logger
from core.point_classes import Point3, Point3Pair, Y_AXIS

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils, attribute_utils, geometry_utils, locator_utils, uv_utils, material_utils

LOGGER = get_logger(__name__, level=logging.INFO)


@dataclass
class StaircaseData:
    start: Point3
    end: Point3
    axis: Axis
    count: int

    def __repr__(self) -> str:
        return (
            f"Start: {self.start}\n"
            f"End: {self.end}\n"
            f"Count: {self.count}\n"
            f"Axis: {self.axis.name}\n"
            f"Rise: {self.rise}\n"
            f"Tread: {self.tread}\n"
        )

    @property
    def data(self) -> dict:
        return {
            "start": self.start.values,
            "end": self.end.values,
            "axis": self.axis.name,
            "count": self.count,
            "rise": self.rise,
            "tread": self.tread,
        }

    @property
    def delta(self) -> Point3:
        return Point3Pair(self.start, self.end).delta

    @property
    def rise(self) -> float:
        return self.delta.y / self.count

    @property
    def tread(self) -> float:
        return self.delta.values[self.axis.value] / (self.count - 1)


class StaircaseCreator:
    def __init__(self, default_rise: float = 20.0, axis: Axis = Axis.z):
        self.default_rise = default_rise
        assert axis in (Axis.x, Axis.z), "Invalid axis"
        self.axis: Axis = axis
        self.data = None
        self._evaluate()

    def _evaluate(self):
        self.locators = [x for x in cmds.ls(sl=True, tr=True) if node_utils.is_locator(x)]
        assert len(self.locators) == 2, "Select two locator"
        positions = [node_utils.get_translation(x) for x in self.locators]
        positions.sort(key=lambda x: x.y)
        start, end = positions
        assert start.y < end.y, "Second locator must be above first"
        assert start.x != end.x and start.z != end.z, "Locators must not be coincident"
        LOGGER.debug(f"Start: {start}\nEnd: {end}")

        # evaluate count based on default tread
        y_delta = end.y - start.y
        count = round(y_delta / self.default_rise)
        LOGGER.debug(y_delta, count)

        self.data = StaircaseData(
            start=start,
            end=end,
            axis=self.axis,
            count=count,
        )

    @property
    def data(self) -> StaircaseData | None:
        return self._data

    @data.setter
    def data(self, value: StaircaseData):
        self._data = value

    def create(self, auto_texture: bool = False):
        """Create the staircase geometry."""
        a_positions = []
        b_positions = []
        for i in range(self.data.count):
            y = self.data.start.y + i * self.data.rise
            if self.axis is Axis.z:
                xa = self.data.start.x
                za = self.data.start.z + i * self.data.tread
                xb = self.data.end.x
                zb = za
            else:
                xa = self.data.start.x + i * self.data.tread
                za = self.data.start.z
                xb = xa
                zb = self.data.end.z
            a_positions.extend([Point3(xa, y, za), Point3(xa, y + self.data.rise, za)])
            b_positions.extend([Point3(xb, y, zb), Point3(xb, y + self.data.rise, zb)])
        spline_a = cmds.curve(
            name="spline_a",
            point=[x.values for x in a_positions],
            degree=1)
        spline_b = cmds.curve(
            name="spline_b",
            point=[x.values for x in b_positions],
            degree=1)
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        stair_geometry, loft = cmds.loft(spline_a, spline_b, degree=1, polygon=1, name="staircase")

        # reverse the staircase normals if the stairs are inside out
        tread_normal = geometry_utils.get_face_normal(node=stair_geometry, face_id=1)
        dot_product = math_funcs.dot_product(vector_a=tread_normal, vector_b=Y_AXIS, normalize=True)
        if dot_product < 0.0:
            cmds.polyNormal(stair_geometry, normalMode=0, userNormalMode=0)

        # add the attributes to the stair geometry so the locators can be recreated.
        attribute_utils.add_attribute(node=stair_geometry, attr="custom_type", data_type=DataType.string,
                                      read_only=True, default_value="staircase")
        attribute_utils.add_attribute(node=stair_geometry, attr="target_rise", data_type=DataType.float,
                                      read_only=False, default_value=self.default_rise)
        axis_index = ["x", "z"].index(self.axis.name)
        attribute_utils.add_enum_attribute(node=stair_geometry, attr="axis", values=["x", "z"], default_index=axis_index)
        cmds.select(stair_geometry)

        # texture the staircase
        if auto_texture:
            material_utils.auto_texture(transform=stair_geometry)

        # clean up
        cmds.polySoftEdge(stair_geometry, angle=0)
        cmds.delete(stair_geometry, constructionHistory=True)
        cmds.delete(spline_a, spline_b, self.locators)
        cmds.select(stair_geometry)
        print(f"Staircase created: {stair_geometry}")


def restore_locators_from_staircase(node: str) -> tuple[list, float, Axis] | None:
    """Recreate the staircase locators from a staircase object."""
    if cmds.attributeQuery("custom_type", node=node, exists=True) and cmds.getAttr(f"{node}.custom_type") == "staircase":
        target_rise = cmds.getAttr(f"{node}.target_rise")
        axis = Axis[["x", "z"][cmds.getAttr(f"{node}.axis")]]
        num_verts = cmds.polyEvaluate(node, vertex=True)
        locator_positions = (
            geometry_utils.get_vertex_position(node=node, vertex_id=0),
            geometry_utils.get_vertex_position(node=node, vertex_id=num_verts - 1)
        )
        locators = []
        for idx, point in enumerate(locator_positions):
            locators.append(locator_utils.create_locator(position=point, name=f"staircase_locator{idx}", size=50.0))
        cmds.delete(node)
        return locators, target_rise, axis
    return None


if __name__ == "__main__":
    if cmds.ls("spline_*"):
        cmds.delete("spline_*")
    if cmds.ls("staircase*"):
        cmds.delete("staircase*")
    cmds.select("locator*")
    stairs = StaircaseCreator(axis=Axis.z)
    print(stairs.data)
    # print(stairs.data.delta)
    stairs.create()