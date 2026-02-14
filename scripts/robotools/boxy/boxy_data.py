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

from core.color_classes import ColorRGB
from core.math_utils import apply_euler_xyz_rotation
from core.point_classes import Point3
from robotools.anchor import Anchor


@dataclass
class BoxyData:
    """Data defining a Boxy node.

    Attributes:
        size: Dimensions of the box (width, height, depth).
        translation: World position where the pivot/transform is placed.
        rotation: Euler XYZ rotation in degrees.
        pivot_anchor: Which anchor point the pivot is on (one of 27 positions).
        color: Wireframe color.
        scale: Optional scale to apply to the transform.
    """
    size: Point3
    translation: Point3
    rotation: Point3
    pivot_anchor: Anchor
    color: ColorRGB
    scale: Point3 = None

    def __post_init__(self):
        if self.scale is None:
            self.scale = Point3(1.0, 1.0, 1.0)

    def __repr__(self) -> str:
        return (
            f"BoxyData(size={self.size}, translation={self.translation}, rotation={self.rotation}, "
            f"pivot={self.pivot_anchor}, color={self.color}, scale={self.scale})"
        )

    @property
    def dictionary(self) -> dict:
        return {
            "size": self.size.values,
            "translation": self.translation.values,
            "rotation": self.rotation.values,
            "pivot_anchor": self.pivot_anchor.name,
            "center": self.center.values,
            "color": self.color.values,
            "scale": self.scale.values,
        }

    def _get_pivot_to_center_offset(self) -> Point3:
        """Calculate offset from pivot position to geometric center.

        Returns the vector that, when added to the pivot position, gives the center.
        This is the negative of the pivot offset from center.
        """
        hx, hy, hz = self.size.x / 2.0, self.size.y / 2.0, self.size.z / 2.0

        # Offset from pivot TO center (negative of pivot offset from center)
        offsets = {
            # Face pivots
            Anchor.f2: Point3(0.0, hy, 0.0),       # bottom -> center is +Y
            Anchor.c: Point3(0.0, 0.0, 0.0),       # center -> center is 0
            Anchor.f3: Point3(0.0, -hy, 0.0),      # top -> center is -Y
            Anchor.f0: Point3(hx, 0.0, 0.0),       # left -> center is +X
            Anchor.f1: Point3(-hx, 0.0, 0.0),      # right -> center is -X
            Anchor.f5: Point3(0.0, 0.0, -hz),      # front -> center is -Z
            Anchor.f4: Point3(0.0, 0.0, hz),       # back -> center is +Z
            # Edge pivots
            Anchor.e0: Point3(0.0, hy, hz),        # bottom-back
            Anchor.e1: Point3(0.0, hy, -hz),       # bottom-front
            Anchor.e2: Point3(0.0, -hy, hz),       # top-back
            Anchor.e3: Point3(0.0, -hy, -hz),      # top-front
            Anchor.e4: Point3(hx, 0.0, hz),        # left-back
            Anchor.e5: Point3(hx, 0.0, -hz),       # left-front
            Anchor.e6: Point3(-hx, 0.0, hz),       # right-back
            Anchor.e7: Point3(-hx, 0.0, -hz),      # right-front
            Anchor.e8: Point3(hx, hy, 0.0),        # left-bottom
            Anchor.e9: Point3(hx, -hy, 0.0),       # left-top
            Anchor.e10: Point3(-hx, hy, 0.0),      # right-bottom
            Anchor.e11: Point3(-hx, -hy, 0.0),     # right-top
            # Vertex pivots
            Anchor.v0: Point3(hx, hy, hz),         # left-bottom-back
            Anchor.v1: Point3(hx, hy, -hz),        # left-bottom-front
            Anchor.v2: Point3(hx, -hy, hz),        # left-top-back
            Anchor.v3: Point3(hx, -hy, -hz),       # left-top-front
            Anchor.v4: Point3(-hx, hy, hz),        # right-bottom-back
            Anchor.v5: Point3(-hx, hy, -hz),       # right-bottom-front
            Anchor.v6: Point3(-hx, -hy, hz),       # right-top-back
            Anchor.v7: Point3(-hx, -hy, -hz),      # right-top-front
        }
        return offsets.get(self.pivot_anchor, Point3(0.0, 0.0, 0.0))

    @property
    def center(self) -> Point3:
        """Calculate the center position from the pivot/translation position.

        The translation is where the pivot is. This calculates where the
        geometric center of the box is based on the pivot anchor.
        """
        local_offset = self._get_pivot_to_center_offset()
        if local_offset.x == 0.0 and local_offset.y == 0.0 and local_offset.z == 0.0:
            return self.translation
        rotated_offset = apply_euler_xyz_rotation(local_offset, self.rotation)
        return Point3(
            self.translation.x + rotated_offset.x,
            self.translation.y + rotated_offset.y,
            self.translation.z + rotated_offset.z
        )
