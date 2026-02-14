"""anchor_utils.py"""
from __future__ import annotations

from maya import cmds

from robotools.anchor import Anchor, index_to_anchor

from core import color_classes, math_utils
from core.color_classes import ColorRGB
from core.point_classes import Point3, ZERO3
from core.bounds import Bounds
from maya_tools import helpers


def get_anchor_offset(anchor: Anchor, hx: float, hy: float, hz: float) -> Point3:
    """Get the local offset from center to an anchor point.

    Args:
        anchor: The anchor point
        hx: Half-extent in X (size.x / 2)
        hy: Half-extent in Y (size.y / 2)
        hz: Half-extent in Z (size.z / 2)

    Returns:
        Point3 local offset from center to anchor
    """
    # Use string keys to avoid enum identity issues with module reloads
    offsets = {
        # Center
        "c": ZERO3,
        # Face centers
        "f0": Point3(-hx, 0.0, 0.0),      # left
        "f1": Point3(hx, 0.0, 0.0),       # right
        "f2": Point3(0.0, -hy, 0.0),      # bottom
        "f3": Point3(0.0, hy, 0.0),       # top
        "f4": Point3(0.0, 0.0, -hz),      # back
        "f5": Point3(0.0, 0.0, hz),       # front
        # Edge midpoints
        "e0": Point3(0.0, -hy, -hz),      # bottom-back
        "e1": Point3(0.0, -hy, hz),       # bottom-front
        "e2": Point3(0.0, hy, -hz),       # top-back
        "e3": Point3(0.0, hy, hz),        # top-front
        "e4": Point3(-hx, 0.0, -hz),      # left-back
        "e5": Point3(-hx, 0.0, hz),       # left-front
        "e6": Point3(hx, 0.0, -hz),       # right-back
        "e7": Point3(hx, 0.0, hz),        # right-front
        "e8": Point3(-hx, -hy, 0.0),      # left-bottom
        "e9": Point3(-hx, hy, 0.0),       # left-top
        "e10": Point3(hx, -hy, 0.0),      # right-bottom
        "e11": Point3(hx, hy, 0.0),       # right-top
        # Vertices
        "v0": Point3(-hx, -hy, -hz),      # left-bottom-back
        "v1": Point3(-hx, -hy, hz),       # left-bottom-front
        "v2": Point3(-hx, hy, -hz),       # left-top-back
        "v3": Point3(-hx, hy, hz),        # left-top-front
        "v4": Point3(hx, -hy, -hz),       # right-bottom-back
        "v5": Point3(hx, -hy, hz),        # right-bottom-front
        "v6": Point3(hx, hy, -hz),        # right-top-back
        "v7": Point3(hx, hy, hz),         # right-top-front
    }
    return offsets.get(anchor.name, ZERO3)


def get_anchor_position_from_bounds(bounds: Bounds, anchor: Anchor) -> Point3:
    """Calculate the world position of an anchor point from bounds.

    The offset from center to anchor is calculated in local space, then
    rotated by the bounds rotation to get the world-space position.

    Args:
        bounds: Bounds object with position, size, rotation, center properties
        anchor: The anchor point to calculate position for

    Returns:
        Point3 world position of the anchor point
    """
    c = bounds.center
    hx, hy, hz = bounds.size.x / 2.0, bounds.size.y / 2.0, bounds.size.z / 2.0

    local_offset = get_anchor_offset(anchor, hx, hy, hz)

    # If no rotation, just add offset directly
    if bounds.rotation.x == 0.0 and bounds.rotation.y == 0.0 and bounds.rotation.z == 0.0:
        return Point3(c.x + local_offset.x, c.y + local_offset.y, c.z + local_offset.z)

    # Rotate the local offset by the bounds rotation
    rotated_offset = math_utils.apply_euler_xyz_rotation(local_offset, bounds.rotation)
    return Point3(c.x + rotated_offset.x, c.y + rotated_offset.y, c.z + rotated_offset.z)


class AnchorComponents:
    """
    Class gets the reference positions of the components
    in a Boxy or Polycube node.
    The reference positions are calculated with the assumption that
    the node sits at the origin with zero rotation and unit scale.
    Those are the values that correspond to what we need for procedural generation.
    """

    def __init__(self, node: str):
        self.node = node
        self.annotations = None

    def __repr__(self) -> str:
        return (
            f"Node: {self.node}"
        )

    @property
    def pivot_offset(self) -> Point3:
        """Location of the pivot relative to the center."""
        hx, hy, hz = self.size.x / 2.0, self.size.y / 2.0, self.size.z / 2.0
        return get_anchor_offset(self.pivot_anchor, hx, hy, hz)

    @property
    def center(self) -> Point3:
        return Point3(*[(self.minimum.values[i] + self.maximum.values[i]) / 2.0 for i in range(3)])

    @property
    def maximum(self) -> Point3:
        return Point3(
            self.size.x / 2.0 - self.pivot_offset.x,
            self.size.y / 2.0 - self.pivot_offset.y,
            self.size.z / 2.0 - self.pivot_offset.z
        )

    @property
    def minimum(self) -> Point3:
        return Point3(
            -self.size.x / 2.0 - self.pivot_offset.x,
            -self.size.y / 2.0 - self.pivot_offset.y,
            -self.size.z / 2.0 - self.pivot_offset.z
        )

    @property
    def pivot_anchor(self) -> Anchor:
        """Get the pivot anchor from the shape node."""
        pivot_index = cmds.getAttr(f"{self.shape}.pivot")
        return index_to_anchor(pivot_index)

    @property
    def edges(self) -> tuple[Point3]:
        """List of edges."""
        return (
            Point3(0.0, self.minimum.y, self.minimum.z),
            Point3(0.0, self.minimum.y, self.maximum.z),
            Point3(0.0, self.maximum.y, self.minimum.z),
            Point3(0.0, self.maximum.y, self.maximum.z),
            Point3(self.minimum.x, self.center.y, self.minimum.z),
            Point3(self.minimum.x, self.center.y, self.maximum.z),
            Point3(self.maximum.x, self.center.y, self.minimum.z),
            Point3(self.maximum.x, self.center.y, self.maximum.z),
            Point3(self.minimum.x, self.minimum.y, 0.0),
            Point3(self.minimum.x, self.maximum.y, 0.0),
            Point3(self.maximum.x, self.minimum.y, 0.0),
            Point3(self.maximum.x, self.maximum.y, 0.0),
        )

    @property
    def faces(self) -> tuple[Point3]:
        """List of faces."""
        return (
            Point3(self.minimum.x, self.center.y, self.center.z),
            Point3(self.maximum.x, self.center.y, self.center.z),
            Point3(self.center.x, self.minimum.y, self.center.z),
            Point3(self.center.x, self.maximum.y, self.center.z),
            Point3(self.center.x, self.center.y, self.minimum.z),
            Point3(self.center.x, self.center.y, self.maximum.z),
        )

    @property
    def vertices(self) -> tuple[Point3]:
        """List of vertices."""
        return (
            Point3(self.minimum.x, self.minimum.y, self.minimum.z),  # 000
            Point3(self.minimum.x, self.minimum.y, self.maximum.z),  # 001
            Point3(self.minimum.x, self.maximum.y, self.minimum.z),  # 010
            Point3(self.minimum.x, self.maximum.y, self.maximum.z),  # 011
            Point3(self.maximum.x, self.minimum.y, self.minimum.z),  # 100
            Point3(self.maximum.x, self.minimum.y, self.maximum.z),  # 101
            Point3(self.maximum.x, self.maximum.y, self.minimum.z),  # 110
            Point3(self.maximum.x, self.maximum.y, self.maximum.z),  # 111
        )

    @property
    def shape(self) -> str:
        return cmds.listRelatives(self.node, shapes=True)[0]

    @property
    def size(self) -> Point3:
        """Size."""
        return Point3(*cmds.getAttr(f"{self.shape}.size")[0])

    def generate_annotations(self):
        """Create annotations at keypoints."""
        annotation_list = [helpers.create_annotation(
            node=self.node,
            text="c",
            color=color_classes.BLACK,
            position=self.center,
            display_arrow=False
        )]
        for idx, vertex in enumerate(self.vertices):
            annotation_list.append(helpers.create_annotation(
                node=self.node,
                text=f"v{idx}",
                color=color_classes.MAROON,
                position=vertex,
                display_arrow=False
            ))
        for idx, edge in enumerate(self.edges):
            annotation_list.append(helpers.create_annotation(
                node=self.node,
                text=f"e{idx}",
                color=color_classes.DARK_BLUE,
                position=edge,
                display_arrow=False
            ))
        for idx, face in enumerate(self.faces):
            annotation_list.append(helpers.create_annotation(
                node=self.node,
                text=f"f{idx}",
                color=color_classes.DARK_GREEN,
                position=face,
                display_arrow=False
            ))

        cmds.group(annotation_list, name="annotations")
        self.annotations = annotation_list


if __name__ == "__main__":
    gen = AnchorComponents(node="boxy")
    print(gen)
    gen.generate_annotations()
    # print(cmds.listRelatives("boxy", shapes=True))
    # locator_utils.create_locator(local_scale=2.0)

    '''locator_utils.create_locator(
        name="test_locator",
        position=Point3(0, 0, 0),
        local_scale=0.2,
        color_rgb=ColorRGB(0, 255, 255),
        annotation="Test Label"
    )'''