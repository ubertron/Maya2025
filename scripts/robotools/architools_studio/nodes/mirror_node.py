"""MirrorNode class for symmetry duplication in procedural templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from robotools.architools_studio.nodes.base_node import BaseNode


@dataclass
class MirrorNode(BaseNode):
    """Applies symmetry duplication to the parent MeshBox.

    A MirrorNode duplicates the parent MeshBox geometry across one or both
    axes (X and Z), creating 2 or 4 instances total. The mirroring is done
    relative to the boxy center.

    Attributes:
        mirror_x: Mirror across X axis (creates copy on opposite X side)
        mirror_z: Mirror across Z axis (creates copy on opposite Z side)

    Instance counts:
        - mirror_x only: 2 instances (original + X-mirrored)
        - mirror_z only: 2 instances (original + Z-mirrored)
        - mirror_x + mirror_z: 4 instances (original + X + Z + XZ diagonal)
    """
    mirror_x: bool = False
    mirror_z: bool = False

    @property
    def node_type(self) -> str:
        return "mirror"

    @property
    def instance_count(self) -> int:
        """Number of instances this mirror creates (including original)."""
        if self.mirror_x and self.mirror_z:
            return 4
        elif self.mirror_x or self.mirror_z:
            return 2
        return 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        base = super().to_dict()
        base.update({
            "mirror_x": self.mirror_x,
            "mirror_z": self.mirror_z,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MirrorNode":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            mirror_x=data.get("mirror_x", False),
            mirror_z=data.get("mirror_z", False),
        )

    def __repr__(self) -> str:
        axes = []
        if self.mirror_x:
            axes.append("X")
        if self.mirror_z:
            axes.append("Z")
        axis_str = "+".join(axes) if axes else "none"
        return f"MirrorNode(name={self.name!r}, axes={axis_str})"
