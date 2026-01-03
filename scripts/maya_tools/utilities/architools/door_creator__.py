# Door Creator
from __future__ import annotations

import math
from dataclasses import dataclass
from maya import cmds

from core.color_classes import WHITE
from core.core_enums import Side, Axis, DataType
from core.point_classes import Point3, Point3Pair, X_AXIS, Z_AXIS
from maya_tools import curve_utils, helpers, material_utils, node_utils
from maya_tools.maya_enums import ObjectType
from maya_tools.utilities.architools.validation import validate_door_curve
from maya_tools.utilities.architools import CURVE_COLOR


@dataclass
class DoorData:
    start: Point3
    end: Point3
    axis: Axis
    door_depth: float
    side: Side
    frame: float
    skirt: float
    angle: float

    def __repr__(self) -> str:
        return (
            f"Start: {self.start}\n"
            f"End: {self.end}\n"
            f"Axis: {self.axis.name}\n"
            f"Doorway Width: {self.doorway_width}\n"
            f"Doorway Height: {self.doorway_height}\n"
            f"Doorway Depth: {self.doorway_depth}\n"
            f"Door Width: {self.door_width}\n"
            f"Door Height: {self.door_height}\n"
            f"Door Depth: {self.door_depth}\n"
            f"Side: {self.side.name}\n"
            f"Frame: {self.frame}\n"
            f"Skirt: {self.skirt}\n"
            f"Angle: {self.angle}\n"
        )

    @property
    def data(self) -> dict:
        return {
            "start": self.start.values,
            "end": self.end.values,
            "axis": self.axis.name,
            "door_thickness": self.door_depth,
            "side": self.side.name,
            "frame": self.frame,
            "skirt": self.skirt,
            "angle": self.angle,
        }

    @property
    def points(self) -> Point3Pair:
        return Point3Pair(self.start, self.end)

    @property
    def delta(self) -> Point3:
        return self.points.delta

    @property
    def door_width(self) -> float:
        doorway_width = self.points.size.x if self.axis is Axis.z else self.points.size.z
        return doorway_width - (2 * self.skirt)

    @property
    def door_frame_bounds(self) -> Point3Pair:
        if self.axis is Axis.z:
            minimum = Point3(
                self.points.minimum.x - self.frame + self.skirt,
                self.points.minimum.y,
                self.points.minimum.z + self.skirt)
            maximum = Point3(
                self.points.maximum.x + self.frame - self.skirt,
                self.points.maximum.y + self.frame - self.skirt,
                self.points.maximum.z - self.skirt
            )
        else:
            minimum = Point3(
                self.points.minimum.x - self.skirt,
                self.points.minimum.y,
                self.points.minimum.z - self.frame + self.skirt)
            maximum = Point3(
                self.points.maximum.x + self.skirt,
                self.points.maximum.y + self.frame - self.skirt,
                self.points.maximum.z + self.frame - self.skirt
            )
        return Point3Pair(minimum, maximum)

    @property
    def doorway_width(self) -> float:
        return self.points.size.x if self.axis is Axis.z else self.points.size.z

    @property
    def doorway_height(self) -> float:
        return self.points.size.y

    @property
    def doorway_depth(self) -> float:
        return self.points.size.values[self.axis.value]

    @property
    def door_height(self) -> float:
        return self.points.size.y - self.skirt

    @property
    def profile_points(self) -> list[Point3]:
        points = []
        if self.axis is Axis.z:
            point = Point3(self.points.minimum.x - self.frame + self.skirt, self.points.minimum.y, self.points.maximum.z)
            points.append(Point3(*point.values))
            point.z = point.z + self.skirt
            points.append(Point3(*point.values))
            point.x = point.x + self.frame
            points.append(Point3(*point.values))
            point.z = point.z - self.doorway_depth - 2 * self.skirt
            points.append(Point3(*point.values))
            point.x = point.x - self.frame
            points.append(Point3(*point.values))
            point.z = point.z + self.skirt
            points.append(Point3(*point.values))
        else:
            point = Point3(self.points.minimum.x, self.points.minimum.y, self.points.minimum.z - self.frame + self.skirt)
            points.append(Point3(*point.values))
            point.x = point.x - self.skirt
            points.append(Point3(*point.values))
            point.z = point.z + self.frame
            points.append(Point3(*point.values))
            point.x = point.x + self.doorway_depth + 2 * self.skirt
            points.append(Point3(*point.values))
            point.z = point.z - self.frame
            points.append(Point3(*point.values))
            point.x = point.x - self.skirt
            points.append(Point3(*point.values))
        return points

    @property
    def profile_positions(self) -> list[Point3]:
        if self.axis is Axis.z:
            return [
                Point3(
                    self.door_frame_bounds.minimum.x,
                    self.door_frame_bounds.minimum.y,
                    self.door_frame_bounds.center.z
                ),
                Point3(
                    self.door_frame_bounds.minimum.x,
                    self.door_frame_bounds.maximum.y,
                    self.door_frame_bounds.center.z
                ),
                Point3(
                    self.door_frame_bounds.maximum.x,
                    self.door_frame_bounds.maximum.y,
                    self.door_frame_bounds.center.z
                ),
                Point3(
                    self.door_frame_bounds.maximum.x,
                    self.door_frame_bounds.minimum.y,
                    self.door_frame_bounds.center.z
                )
            ]
        else:
            return [
                Point3(
                    self.door_frame_bounds.center.x,
                    self.door_frame_bounds.minimum.y,
                    self.door_frame_bounds.minimum.z
                ),
                Point3(
                    self.door_frame_bounds.center.x,
                    self.door_frame_bounds.maximum.y,
                    self.door_frame_bounds.minimum.z
                ),
                Point3(
                    self.door_frame_bounds.center.x,
                    self.door_frame_bounds.maximum.y,
                    self.door_frame_bounds.maximum.z
                ),
                Point3(
                    self.door_frame_bounds.center.x,
                    self.door_frame_bounds.minimum.y,
                    self.door_frame_bounds.maximum.z
                )
            ]

class DoorCreator:
    def __init__(self, skirt: float, frame: float, door_thickness: float = 5.0, axis: Axis = Axis.z,
                 opening_side: Side = Side.front, hinge_side: Side = Side.left, rotation: float = 0.0):
        assert axis in (Axis.x, Axis.z), "Invalid axis"
        assert opening_side in (Side.front, Side.back), "Invalid side"
        assert hinge_side in (Side.left, Side.right), "Invalid side"
        self.skirt = skirt
        self.frame = frame
        self.door_thickness = door_thickness
        self.opening_side = opening_side
        self.rotation = rotation
        self._validate()
        print(self.data)

    @property
    def data(self) -> DoorData:
        return self._data

    def _validate(self):
        """Initialize the data from the locators."""
        self.locators = [x for x in cmds.ls(sl=True, tr=True) if node_utils.is_locator(x)]
        assert len(self.locators) == 2, "Select two locators"
        positions = [node_utils.get_translation(x) for x in self.locators]
        positions.sort(key=lambda x: x.y)
        start, end = positions

        # validate minimum bounds for locators

        # evaluate axis based on locator positions
        horizontal_vector = Point3Pair(Point3(start.x, 0, start.z), Point3(end.x, 0, end.z)).delta
        dot_product_x = Point3Pair(horizontal_vector, X_AXIS).dot_product
        dot_product_z = Point3Pair(horizontal_vector, Z_AXIS).dot_product
        axis = Axis.x if abs(dot_product_x) < abs(dot_product_z) else Axis.z

        self._data = DoorData(
            start=start,
            end=end,
            axis=axis,
            door_depth=self.door_thickness,
            side=self.side,
            frame=self.frame,
            skirt=self.skirt,
            angle=self.rotation,
        )

    def create(self, auto_texture: bool = False) -> DoorData:
        """Create the door geometry."""
        # create first profile
        for x in self.data.profile_points:
            print(x)

        # create the door curves
        door_curves = [curve_utils.create_curve_from_points(
            points=self.data.profile_points, close=False, name="door_curve0", color=CURVE_COLOR)]
        node_utils.set_pivot(nodes=door_curves[0], value=self.data.profile_positions[0])

        for i in range(1, 4):
            door_curves.append(node_utils.duplicate(node=door_curves[0], name=f"door_curve{i}"))
            node_utils.set_translation(nodes=door_curves[i], value=self.data.profile_positions[i])

        if self.data.axis == Axis.z:
            cmds.setAttr(f"{door_curves[1]}.rotateZ", -45)
            cmds.setAttr(f"{door_curves[1]}.scaleX", math.sqrt(2))
            cmds.setAttr(f"{door_curves[2]}.rotateZ", -135)
            cmds.setAttr(f"{door_curves[2]}.scaleX", math.sqrt(2))
            cmds.setAttr(f"{door_curves[3]}.rotateZ", -180)
        else:
            cmds.setAttr(f"{door_curves[1]}.rotateX", 45)
            cmds.setAttr(f"{door_curves[1]}.scaleZ", math.sqrt(2))
            cmds.setAttr(f"{door_curves[2]}.rotateX", 135)
            cmds.setAttr(f"{door_curves[2]}.scaleZ", math.sqrt(2))
            cmds.setAttr(f"{door_curves[3]}.rotateX", 180)

        # create the geometry
        cmds.nurbsToPolygonsPref(polyType=1, format=3)
        door_frame, loft = cmds.loft(*door_curves, degree=1, polygon=1, name="door_frame")

        # attributes
        attribute_utils.add_attribute(node=door_frame, attr="custom_type", data_type=DataType.string,
                                      lock=True, default_value="door")
        attribute_utils.add_attribute(node=door_frame, attr="trim", data_type=DataType.float,
                                      lock=False, default_value=self.skirt)
        attribute_utils.add_attribute(node=door_frame, attr="frame", data_type=DataType.float,
                                      lock=False, default_value=self.frame)

        # texture
        if auto_texture:
            material_utils.auto_texture(transform=door_frame)

        # cleanup
        cmds.polySoftEdge(door_frame, angle=0)
        node_utils.pivot_to_base(node=door_frame)
        cmds.delete(door_frame, constructionHistory=True)
        cmds.delete(door_curves, self.locators)
        cmds.select(door_frame)
