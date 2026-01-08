from dataclasses import dataclass

from core.point_classes import Point3, Point3Pair
from maya_tools.utilities.architools.arch_data import ArchData


@dataclass
class WindowData(ArchData):
    sill_thickness: float
    sill_depth: float

    def __repr__(self):
        return (
            f"Position: {self.translation}\n"
            f"Rotation: {self.y_rotation}\n"
            f"Size: {self.size}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f"Sill Thickness: {self.sill_thickness}\n"
            f"Sill Depth: {self.sill_depth}\n"
        )


TEST_WINDOW_DATA: WindowData = WindowData(
    translation=Point3(20.5, 0.0, -4.2),
    y_rotation=45.0,
    size=Point3(150.0, 90.0, 25.0),
    sill_thickness=2.0,
    sill_depth=4.0
)

if __name__ == "__main__":
    print(TEST_WINDOW_DATA)
