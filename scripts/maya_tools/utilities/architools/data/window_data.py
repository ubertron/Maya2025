from dataclasses import dataclass

from core.point_classes import Point3, Point3Pair
from maya_tools.utilities.architools.data.arch_data import ArchData


@dataclass
class WindowData(ArchData):
    """Class contains all the data necessary to construct a window object."""
    sill_thickness: float
    sill_depth: float
    frame: float
    skirt: float

    def __repr__(self):
        return (
            f"Position: {self.translation}\n"
            f"Rotation: {self.y_rotation}\n"
            f"Size: {self.size}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f'{"-" * 26}\n'
            f"Sill Thickness: {self.sill_thickness}\n"
            f"Sill Depth: {self.sill_depth}\n"
            f"Frame: {self.frame}\n"
            f"Skirt: {self.skirt}\n"
        )

    @property
    def frame_bounds(self) -> Point3Pair:
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
    def sill_size(self) -> Point3:
        """Size of the window sill."""
        return Point3(
            self.bounds.size.x + 2 * self.frame,
            self.sill_thickness,
            self.bounds.size.z + 2 * self.sill_depth
        )

    @property
    def opening_depth(self) -> float:
        """Depth of the opening."""
        return self.bounds.size.z

    @property
    def window_frame_profile_points(self) -> list[Point3]:
        """Control Vertex positions for profile curve."""
        points = []
        point = Point3(
            self.bounds.minimum.x - self.frame + self.skirt,
            self.bounds.minimum.y,
            self.bounds.maximum.z)
        points.append(Point3(*point.values))
        point.z = point.z + self.skirt
        points.append(Point3(*point.values))
        point.x = point.x + self.frame
        points.append(Point3(*point.values))
        point.z = point.z - self.opening_depth - 2 * self.skirt
        points.append(Point3(*point.values))
        point.x = point.x - self.frame
        points.append(Point3(*point.values))
        point.z = point.z + self.skirt
        points.append(Point3(*point.values))
        return points

    @property
    def window_frame_profile_positions(self) -> list[Point3]:
        """Positions of the four profile curves of the window frame."""
        return [
            Point3(
                self.frame_bounds.minimum.x,
                self.frame_bounds.minimum.y,
                self.frame_bounds.center.z
            ),
            Point3(
                self.frame_bounds.minimum.x,
                self.frame_bounds.maximum.y,
                self.frame_bounds.center.z
            ),
            Point3(
                self.frame_bounds.maximum.x,
                self.frame_bounds.maximum.y,
                self.frame_bounds.center.z
            ),
            Point3(
                self.frame_bounds.maximum.x,
                self.frame_bounds.minimum.y,
                self.frame_bounds.center.z
            )
        ]

    @property
    def window_frame_profile_rotations(self) -> list[float]:
        """Rotations of the four profile curves of the window frame."""
        return [0.0, -45.0, -135.0, -180.0]


TEST_WINDOW_DATA: WindowData = WindowData(
    translation=Point3(20.5, 0.0, -4.2),
    y_rotation=45.0,
    size=Point3(150.0, 90.0, 25.0),
    sill_thickness=2.0,
    sill_depth=4.0,
    frame=20.0,
    skirt=2.0,
)

if __name__ == "__main__":
    print(TEST_WINDOW_DATA)
