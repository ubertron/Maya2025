"""OffsetNode class for position offset modifiers in procedural templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from robotools.architools_studio.nodes.base_node import BaseNode


@dataclass
class OffsetNode(BaseNode):
    """Applies a position offset to the parent MeshBox.

    An OffsetNode is a child modifier that shifts the parent MeshBox's
    position by a fixed amount on each axis. The offset is applied after
    the MeshBox is positioned at its anchor point on the Boxy.

    Attributes:
        offset_x: X-axis offset in scene units (positive = right)
        offset_y: Y-axis offset in scene units (positive = up)
        offset_z: Z-axis offset in scene units (positive = forward)
    """
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0

    @property
    def node_type(self) -> str:
        return "offset"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        base = super().to_dict()
        base.update({
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "offset_z": self.offset_z,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OffsetNode":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            offset_x=data.get("offset_x", 0.0),
            offset_y=data.get("offset_y", 0.0),
            offset_z=data.get("offset_z", 0.0),
        )

    def __repr__(self) -> str:
        return (
            f"OffsetNode(name={self.name!r}, "
            f"offset=[{self.offset_x}, {self.offset_y}, {self.offset_z}])"
        )
