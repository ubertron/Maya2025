"""Arch Data

Dataclass to handle all the information required to create an Architools asset
"""

from dataclasses import dataclass

from core.point_classes import Point3, Point3Pair
from core.core_enums import CustomType


@dataclass
class ArchData:
    translation: Point3  # translation of the object from the origin
    y_rotation: float  # y-axis rotation of the object
    size: Point3  # size of space to create the asset in

    @property
    def delta(self) -> Point3:
        return self.bounds.delta

    @property
    def bounds(self) -> Point3Pair:
        return Point3Pair(
            a=Point3(-self.size.x / 2.0, 0.0, -self.size.z / 2.0),
            b=Point3(self.size.x / 2.0, self.size.y, self.size.z / 2.0),
        )
