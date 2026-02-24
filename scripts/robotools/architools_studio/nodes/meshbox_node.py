"""MeshBoxNode class for geometry primitives in procedural templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from robotools.anchor import Anchor
from robotools.architools_studio.nodes.base_node import BaseNode
from robotools.architools_studio.nodes.size_value import SizeValue, SizeMode


@dataclass
class MeshBoxNode(BaseNode):
    """Defines a MeshBox primitive relative to a Boxy reference.

    A MeshBoxNode represents a rectangular box that is positioned and sized
    relative to the linked Boxy node. It can have child modifier nodes
    (Offset, Mirror) that further transform the geometry.

    Attributes:
        pivot_anchor: Where the MeshBox pivot is placed (from 27 anchor positions)
        position_anchor: Where on the Boxy this MeshBox is anchored
        width: X dimension (SizeValue - constant, max, or linked)
        height: Y dimension (SizeValue - constant, max, or linked)
        depth: Z dimension (SizeValue - constant, max, or linked)
        children: List of child modifier node IDs (Offset, Mirror)
        maya_uuid: Maya scene node UUID (session-only, not serialized)
        mirror_uuids: Maya UUIDs for mirrored geometry (session-only, not serialized)
    """
    pivot_anchor: Anchor = Anchor.c
    position_anchor: Anchor = Anchor.c
    width: SizeValue = field(default_factory=lambda: SizeValue.constant(50.0))
    height: SizeValue = field(default_factory=lambda: SizeValue.constant(50.0))
    depth: SizeValue = field(default_factory=lambda: SizeValue.constant(50.0))
    children: list[str] = field(default_factory=list)
    maya_uuid: str | None = field(default=None, repr=False)  # Session-only, not serialized
    mirror_uuids: list[str] = field(default_factory=list, repr=False)  # Session-only, not serialized

    @property
    def node_type(self) -> str:
        return "meshbox"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        base = super().to_dict()
        base.update({
            "pivot_anchor": self.pivot_anchor.name,
            "position_anchor": self.position_anchor.name,
            "width": self.width.to_dict(),
            "height": self.height.to_dict(),
            "depth": self.depth.to_dict(),
            "children": self.children.copy(),
        })
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MeshBoxNode":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            pivot_anchor=Anchor[data.get("pivot_anchor", "c")],
            position_anchor=Anchor[data.get("position_anchor", "c")],
            width=SizeValue.from_dict(data.get("width", {"mode": "constant", "value": 50.0})),
            height=SizeValue.from_dict(data.get("height", {"mode": "constant", "value": 50.0})),
            depth=SizeValue.from_dict(data.get("depth", {"mode": "constant", "value": 50.0})),
            children=data.get("children", []),
        )

    def add_child(self, child_id: str) -> None:
        """Add a child modifier node ID."""
        if child_id not in self.children:
            self.children.append(child_id)

    def remove_child(self, child_id: str) -> None:
        """Remove a child modifier node ID."""
        if child_id in self.children:
            self.children.remove(child_id)

    def set_size_constant(self, width: float, height: float, depth: float) -> None:
        """Set all dimensions to constant values."""
        self.width = SizeValue.constant(width)
        self.height = SizeValue.constant(height)
        self.depth = SizeValue.constant(depth)

    def set_size_max(self) -> None:
        """Set all dimensions to match boxy (max mode)."""
        self.width = SizeValue.max_size()
        self.height = SizeValue.max_size()
        self.depth = SizeValue.max_size()

    def get_parameter_references(self) -> list[str]:
        """Get all parameter names referenced by this node's dimensions."""
        params = []
        for size_value in [self.width, self.height, self.depth]:
            param_name = size_value.get_parameter_name()
            if param_name:
                params.append(param_name)
        return params

    def __repr__(self) -> str:
        return (
            f"MeshBoxNode(name={self.name!r}, "
            f"pivot={self.pivot_anchor.name}, "
            f"position={self.position_anchor.name}, "
            f"size=[{self.width}, {self.height}, {self.depth}])"
        )
