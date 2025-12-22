"""ArchData subclass for DoorCreator."""

from __future__ import annotations

from dataclasses import dataclass

from core.core_enums import Axis, Side
from core.point_classes import Point3, Point3Pair
from maya_tools.utilities.architools.arch_data import ArchData


@dataclass
class DoorData(ArchData):
    """Class contains all the data necessary to construct a door object."""

    door_depth: float
    hinge_side: Side
    opening_side: Side
    frame: float
    skirt: float

    def __repr__(self) -> str:
        return (
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation}\n"
            f"Size: {self.size}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f"Door Width: {self.door_width}\n"
            f"Door Height: {self.door_height}\n"
            f"Door Depth: {self.door_depth}\n"
            f"Hinge Side: {self.hinge_side.name}\n"
            f"Opening Side: {self.opening_side.name}\n"
            f"Frame Size: {self.frame}\n"
            f"Skirt: {self.skirt}\n"
        )

    @property
    def data(self) -> dict:
        return {
            "position": self.position,
            "rotation": self.rotation,
            "start": self.bounds.a.values,
            "end": self.bounds.b.values,
            "door_depth": self.door_depth,
            "hinge_side": self.hinge_side.name,
            "opening_side": self.opening_side.name,
            "frame": self.frame,
            "skirt": self.skirt,
        }

    @property
    def door_width(self) -> float:
        return self.size.x - (2 * self.skirt)

    @property
    def door_frame_bounds(self) -> Point3Pair:
        minimum = Point3(
            self.bounds.minimum.x - self.frame + self.skirt,
            self.bounds.minimum.y,
            self.bounds.minimum.z + self.skirt)
        maximum = Point3(
            self.bounds.maximum.x + self.frame - self.skirt,
            self.bounds.maximum.y + self.frame - self.skirt,
            self.bounds.maximum.z - self.skirt
        )
        return Point3Pair(minimum, maximum)

    @property
    def door_height(self) -> float:
        return self.size.y - self.skirt

    @property
    def doorway_depth(self) -> float:
        return self.bounds.size.z

    @property
    def doorway_profile_points(self) -> list[Point3]:
        """Control Vertex positions for profile curve."""
        points = []
        point = Point3(self.bounds.minimum.x - self.frame + self.skirt, self.bounds.minimum.y, self.bounds.maximum.z)
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
        return points

    @property
    def doorway_profile_positions(self) -> list[Point3]:
        """Positions of the four profile curves of the doorway."""
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
    @property
    def doorway_profile_rotations(self) -> list[float]:
        """Rotations of the four profile curves of the doorway."""
        return [0.0, -45.0, -135.0, -180.0]


TEST_DOOR_DATA = DoorData(
    position=Point3(2.4, 0.0, -4.2),
    rotation=30.0,
    size=Point3(95.0, 205.0, 30.0),
    door_depth=5.0,
    hinge_side=Side.left,
    opening_side=Side.front,
    frame=10.0,
    skirt=2.0,
)


if __name__ == "__main__":
    print(TEST_DOOR_DATA)
    print(TEST_DOOR_DATA.data)
    print(TEST_DOOR_DATA.door_frame_bounds)
