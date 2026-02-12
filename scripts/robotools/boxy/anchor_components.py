"""anchor_components.py"""
from __future__ import annotations

from importlib import reload
from maya import cmds

from robotools.boxy import boxy_utils
from robotools.anchor import Anchor

from core.core_enums import Side
from core import color_classes
from core.color_classes import ColorRGB
from core.point_classes import Point3, ZERO3
from maya_tools import helpers


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
        return {
            Side.center: ZERO3,
            Side.left: Point3(-self.size.x, 0.0, 0.0),
            Side.right: Point3(self.size.x, 0.0, 0.0),
            Side.top: Point3(0.0, self.size.y / 2.0, 0.0),
            Side.bottom: Point3(0.0, -self.size.y / 2.0, 0.0),
            Side.front: Point3(0.0, 0.0, self.size.z / 2.0),
            Side.back: Point3(0.0, 0.0, -self.size.z / 2.0),
        }[self.pivot_side]

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
    def pivot_side(self) -> Side:
        return Side[cmds.getAttr(f"{self.shape}.pivot", asString=True)]

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