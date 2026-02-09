from __future__ import annotations

from enum import Enum, auto


class CustomAttribute(Enum):
    custom_type = auto()
    door_depth = auto()
    frame = auto()
    hinge_side = auto()
    opening_side = auto()
    pivot_side = auto()
    sill_depth = auto()
    sill_thickness = auto()
    size = auto()
    skirt = auto()
    target_rise = auto()


class CustomType(Enum):
    boxy = auto()
    polycube = auto()
    door = auto()
    staircase = auto()
    window = auto()
