from dataclasses import dataclass

from core.point_classes import Point3
from maya_tools.utilities.architools.data.arch_data import ArchData


@dataclass
class WindowData(ArchData):
    """Class contains all the data necessary to construct a window object."""
    sill_thickness: float
    sill_depth: float
    frame: float
    skirt: float

    def __repr__(self):
        return (
            f"Position: {self.translation}\n"
            f"Rotation: {self.y_rotation}\n"
            f"Size: {self.size}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f'{"-" * 26}\n'
            f"Sill Thickness: {self.sill_thickness}\n"
            f"Sill Depth: {self.sill_depth}\n"
            f"Frame: {self.frame}\n"
            f"Skirt: {self.skirt}\n"
        )


TEST_WINDOW_DATA: WindowData = WindowData(
    translation=Point3(20.5, 0.0, -4.2),
    y_rotation=45.0,
    size=Point3(150.0, 90.0, 25.0),
    sill_thickness=2.0,
    sill_depth=4.0,
    frame=20.0,
    skirt=2.0,
)

if __name__ == "__main__":
    print(TEST_WINDOW_DATA)
