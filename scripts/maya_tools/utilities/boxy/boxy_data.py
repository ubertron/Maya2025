"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
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
        scale: Optional scale to apply to the transform.
    """
    size: Point3
    translation: Point3
    rotation: Point3
    pivot_side: Side
    color: RGBColor
    scale: Point3 = None

    def __post_init__(self):
        if self.scale is None:
            self.scale = Point3(1.0, 1.0, 1.0)

    def __repr__(self) -> str:
        return (
            f"BoxyData(size={self.size}, translation={self.translation}, rotation={self.rotation}, "
            f"pivot={self.pivot_side}, color={self.color}, scale={self.scale})"
        )

    @property
    def dictionary(self) -> dict:
        return {
            "size": self.size.values,
            "translation": self.translation.values,
            "rotation": self.rotation.values,
            "pivot_side": self.pivot_side.name,
            "center": self.center.values,
            "color": self.color.values,
            "scale": self.scale.values,
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
