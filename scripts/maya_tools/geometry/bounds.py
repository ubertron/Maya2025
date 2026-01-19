from __future__ import annotations

from dataclasses import dataclass

from core.math_utils import apply_euler_xyz_rotation
from core.point_classes import Point3


@dataclass
class Bounds:
    """Dataclass to represent a bounding box in space."""
    size: Point3
    position: Point3
    rotation: Point3

    @property
    def base_center(self) -> Point3:
        """
        Calculate the center point of the bottom face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the bottom face center.
        """
        # Local offset from center to base center (before rotation)
        local_offset = Point3(0.0, -self.size.y / 2.0, 0.0)

        # Apply rotation to the offset
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)

        # Add to world position
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )

    @property
    def top_center(self) -> Point3:
        """
        Calculate the center point of the top face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the top face center.
        """
        # Local offset from center to top center (before rotation)
        local_offset = Point3(0.0, self.size.y / 2.0, 0.0)

        # Apply rotation to the offset
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)

        # Add to world position
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )
