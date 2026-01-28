from __future__ import annotations

from dataclasses import dataclass

from core.color_classes import RGBColor
from core.core_enums import Side
from core.math_utils import apply_euler_xyz_rotation
from core.point_classes import Point3


@dataclass
class BoxyData:
    """Data defining a Boxy node.

    Attributes:
        size: Dimensions of the box (width, height, depth).
        translation: World position where the pivot/transform is placed.
        rotation: Euler XYZ rotation in degrees.
        pivot_side: Which side of the box the pivot is on.
        color: Wireframe color.
    """
    size: Point3
    translation: Point3
    rotation: Point3
    pivot_side: Side
    color: RGBColor

    def __repr__(self) -> str:
        return f"BoxyData(size={self.size}, translation={self.translation}, rotation={self.rotation}, pivot={self.pivot_side}, color={self.color})"

    @property
    def dictionary(self) -> dict:
        return {
            "size": self.size.values,
            "translation": self.translation.values,
            "rotation": self.rotation.values,
            "pivot_side": self.pivot_side.name,
            "center": self.center.values,
            "color": self.color.values,
        }

    @property
    def center(self) -> Point3:
        """Calculate the center position from the pivot/translation position.

        The translation is where the pivot is. This calculates where the
        geometric center of the box is based on the pivot side.
        """
        pivot_to_center_offsets = {
            Side.bottom: Point3(0.0, self.size.y / 2.0, 0.0),
            Side.top: Point3(0.0, -self.size.y / 2.0, 0.0),
            Side.left: Point3(self.size.x / 2.0, 0.0, 0.0),
            Side.right: Point3(-self.size.x / 2.0, 0.0, 0.0),
            Side.front: Point3(0.0, 0.0, -self.size.z / 2.0),
            Side.back: Point3(0.0, 0.0, self.size.z / 2.0),
            Side.center: Point3(0.0, 0.0, 0.0),
        }
        local_offset = pivot_to_center_offsets[self.pivot_side]
        if local_offset.x == 0.0 and local_offset.y == 0.0 and local_offset.z == 0.0:
            return self.translation
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.translation.x + rotated_offset.x,
            self.translation.y + rotated_offset.y,
            self.translation.z + rotated_offset.z
        )
