from __future__ import annotations

from dataclasses import dataclass

from core.core_enums import Side
from core.math_utils import apply_euler_xyz_rotation
from core.point_classes import Point3, Point3Pair


@dataclass
class Bounds:
    """Dataclass to represent a bounding box in space."""
    size: Point3
    position: Point3
    rotation: Point3

    @property
    def back(self) -> Point3:
        """
        Calculate the center point of the back face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the back face center.
        """
        local_offset = Point3(0.0, 0.0, -self.size.z / 2.0)
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )

    @property
    def bottom(self) -> Point3:
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
    def center(self) -> Point3:
        """Alias for position, for consistency with Point3Pair."""
        return self.position

    @property
    def front(self) -> Point3:
        """
        Calculate the center point of the front face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the front face center.
        """
        local_offset = Point3(0.0, 0.0, self.size.z / 2.0)
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )

    @property
    def left(self) -> Point3:
        """
        Calculate the center point of the left face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the left face center.
        """
        local_offset = Point3(-self.size.x / 2.0, 0.0, 0.0)
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )

    @property
    def right(self) -> Point3:
        """
        Calculate the center point of the right face of the bounding box.

        Accounts for rotation by transforming the local offset to world space.

        Returns:
            Point3: World-space position of the right face center.
        """
        local_offset = Point3(self.size.x / 2.0, 0.0, 0.0)
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.position.x + rotated_offset.x,
            self.position.y + rotated_offset.y,
            self.position.z + rotated_offset.z
        )

    @property
    def top(self) -> Point3:
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

    def get_pivot(self, side: Side) -> Point3:
        """Position of the pivot given by side."""
        return {
            Side.back: self.back,
            Side.bottom: self.bottom,
            Side.center: self.center,
            Side.front: self.front,
            Side.left: self.left,
            Side.right: self.right,
            Side.top: self.top,
        }[side]