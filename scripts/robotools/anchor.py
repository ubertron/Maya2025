from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.core_enums import Side


class Anchor(Enum):
    c = "center"
    e0 = auto()
    e1 = auto()
    e2 = auto()
    e3 = auto()
    e4 = auto()
    e5 = auto()
    e6 = auto()
    e7 = auto()
    e8 = auto()
    e9 = auto()
    e10 = auto()
    e11 = auto()
    f0 = "left"
    f1 = "right"
    f2 = "bottom"
    f3 = "top"
    f4 = "back"
    f5 = "front"
    v0 = auto()
    v1 = auto()
    v2 = auto()
    v3 = auto()
    v4 = auto()
    v5 = auto()
    v6 = auto()
    v7 = auto()


# Basic anchors correspond to the original 7 Side-based pivot positions
BASIC_ANCHORS = (Anchor.c, Anchor.f0, Anchor.f1, Anchor.f2, Anchor.f3, Anchor.f4, Anchor.f5)
BASIC_ANCHOR_NAMES = {'c', 'f0', 'f1', 'f2', 'f3', 'f4', 'f5'}


def is_basic_anchor(anchor: Anchor) -> bool:
    """Returns True if anchor is one of the 7 basic positions (center + faces).

    Uses string comparison to avoid module reload issues with enum identity.
    """
    return anchor.name in BASIC_ANCHOR_NAMES


def anchor_to_side(anchor: Anchor) -> Side | None:
    """Convert basic anchor to Side enum for backward compatibility.

    Returns None for edge/vertex anchors which have no Side equivalent.
    Uses string keys to avoid module reload issues with enum identity.
    """
    from core.core_enums import Side
    mapping = {
        'c': Side.center,
        'f0': Side.left,
        'f1': Side.right,
        'f2': Side.bottom,
        'f3': Side.top,
        'f4': Side.back,
        'f5': Side.front,
    }
    return mapping.get(anchor.name)


def side_to_anchor(side: Side) -> Anchor:
    """Convert Side enum to Anchor for migration from old system.

    Uses string keys to avoid module reload issues with enum identity.
    """
    from core.core_enums import Side
    mapping = {
        'center': Anchor.c,
        'left': Anchor.f0,
        'right': Anchor.f1,
        'bottom': Anchor.f2,
        'top': Anchor.f3,
        'back': Anchor.f4,
        'front': Anchor.f5,
    }
    return mapping[side.name]


def anchor_to_index(anchor: Anchor) -> int:
    """Convert Anchor to Maya plugin pivot attribute index.

    Maintains backward compatibility with existing indices 0-6.
    Uses string keys to avoid module reload issues with enum identity.
    """
    mapping = {
        'f2': 0,   # bottom
        'c': 1,    # center
        'f3': 2,   # top
        'f0': 3,   # left
        'f1': 4,   # right
        'f5': 5,   # front
        'f4': 6,   # back
        'e0': 7, 'e1': 8, 'e2': 9, 'e3': 10,
        'e4': 11, 'e5': 12, 'e6': 13, 'e7': 14,
        'e8': 15, 'e9': 16, 'e10': 17, 'e11': 18,
        'v0': 19, 'v1': 20, 'v2': 21, 'v3': 22,
        'v4': 23, 'v5': 24, 'v6': 25, 'v7': 26,
    }
    return mapping[anchor.name]


def index_to_anchor(index: int) -> Anchor:
    """Convert Maya plugin pivot attribute index to Anchor."""
    mapping = {
        0: Anchor.f2,   # bottom
        1: Anchor.c,    # center
        2: Anchor.f3,   # top
        3: Anchor.f0,   # left
        4: Anchor.f1,   # right
        5: Anchor.f5,   # front
        6: Anchor.f4,   # back
        7: Anchor.e0, 8: Anchor.e1, 9: Anchor.e2, 10: Anchor.e3,
        11: Anchor.e4, 12: Anchor.e5, 13: Anchor.e6, 14: Anchor.e7,
        15: Anchor.e8, 16: Anchor.e9, 17: Anchor.e10, 18: Anchor.e11,
        19: Anchor.v0, 20: Anchor.v1, 21: Anchor.v2, 22: Anchor.v3,
        23: Anchor.v4, 24: Anchor.v5, 25: Anchor.v6, 26: Anchor.v7,
    }
    return mapping[index]
