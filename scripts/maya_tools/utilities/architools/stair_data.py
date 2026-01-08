from dataclasses import dataclass

from core.core_enums import Axis
from core.point_classes import Point3, Point3Pair, X_AXIS, Z_AXIS
from maya_tools.utilities.architools.arch_data import ArchData


@dataclass
class StairData(ArchData):
    """Class contains all the data necessary to construct a door object."""

    count: int

    def __repr__(self):
        return (
            f"Position: {self.translation}\n"
            f"Rotation: {self.y_rotation}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f"Count: {self.count}\n"
            f"rise: {self.rise}\n"
            f"tread: {self.tread}\n"
        )

    @property
    def data(self) -> dict:
        return {
            "position": self.translation,
            "rotation": self.y_rotation,
            "start": self.bounds.a.values,
            "end": self.bounds.b.values,
            "count": self.count,
            "rise": self.rise,
            "tread": self.tread,
        }

    @property
    def rise(self) -> float:
        return self.size.y / self.count

    @property
    def tread(self) -> float:
        return self.size.z / (self.count - 1)


TEST_STAIR_DATA = StairData(
    translation=Point3(2.4, 0.0, -4.2),
    y_rotation=30.0,
    size=Point3(95.0, 205.0, 240.0),
    count=14,
)


if __name__ == "__main__":
    print(TEST_STAIR_DATA)
    print(TEST_STAIR_DATA.data)
