# Staircase Creator
from __future__ import annotations
import contextlib
from dataclasses import dataclass

from core.core_enums import Axis
from core.point_classes import Point3, Point3Pair

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils


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
        self.axis = axis
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
        print(f"Start: {start}\nEnd: {end}")

        # evaluate count based on default tread
        y_delta = end.y - start.y
        count = round(y_delta / self.default_rise)
        print(y_delta, count)

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

    def create(self):
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
        if (self.axis is Axis.z and self.data.end.x > self.data.start.x) or \
                self.data.end.z > self.data.start.z:
            a_positions.reverse()
            b_positions.reverse()
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
        cmds.polySoftEdge(stair_geometry, angle=0)
        cmds.delete(stair_geometry, constructionHistory=True)
        cmds.delete(spline_a, spline_b)
        cmds.select(self.locators)
        print(f"Staircase create: {stair_geometry}")
        # add the attributes to the stair geometry so the locators can be recreated.


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