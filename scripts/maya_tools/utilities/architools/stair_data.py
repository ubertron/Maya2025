from dataclasses import dataclass

from core.core_enums import Axis
from maya_tools.utilities.architools.arch_data import ArchData


@dataclass
class StairData(ArchData):
    axis: Axis  # stairs can run along two axes: X or Z
    climb: bool  # do stairs rise or fall along axis?

    def __repr__(self):
        return (
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation}\n"
            f"Start: {self.bounds.a}\n"
            f"End: {self.bounds.b}\n"
            f"Axis: {self.axis.name}\n"
            f"Climb: {self.climb}\n"
        )
