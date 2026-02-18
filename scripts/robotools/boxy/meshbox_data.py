from dataclasses import dataclass

from core.point_classes import Point3
from robotools.anchor import Anchor


@dataclass
class MeshboxData:
    """Data defining a Meshbox node.

    Attributes:
        size: Dimensions of the box (width, height, depth).
        translation: World position where the pivot/transform is placed.
        rotation: Euler XYZ rotation in degrees.
        pivot_anchor: Which anchor point the pivot is on (one of 27 positions).
        scale: Optional scale to apply to the transform.
    """
    size: Point3
    pivot_anchor: Anchor
    translation: Point3
    rotation: Point3
    scale: Point3 = None
