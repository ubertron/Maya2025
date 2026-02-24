"""ParameterNode class for exposed parameters in procedural templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from robotools.architools_studio.nodes.base_node import BaseNode


@dataclass
class ParameterNode(BaseNode):
    """Defines an exposed parameter for the template.

    Parameters allow users to customize the generated geometry through
    sliders in the UI. MeshBox dimensions can reference parameters using
    the "$param_name" syntax in SizeValue.

    Attributes:
        default_value: Default parameter value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        step: Increment step for UI slider
        current_value: Current value (session-only, defaults to default_value)
    """
    default_value: float = 10.0
    min_value: float = 1.0
    max_value: float = 100.0
    step: float = 1.0
    current_value: float | None = field(default=None, repr=False)  # Session-only

    def __post_init__(self):
        """Initialize current_value to default if not set."""
        if self.current_value is None:
            self.current_value = self.default_value

    @property
    def node_type(self) -> str:
        return "parameter"

    @property
    def value(self) -> float:
        """Get the current value (or default if not set)."""
        return self.current_value if self.current_value is not None else self.default_value

    @value.setter
    def value(self, val: float):
        """Set the current value, clamping to min/max."""
        self.current_value = max(self.min_value, min(self.max_value, val))

    def reset(self):
        """Reset current value to default."""
        self.current_value = self.default_value

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        base = super().to_dict()
        base.update({
            "default_value": self.default_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "step": self.step,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParameterNode":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            default_value=data.get("default_value", 10.0),
            min_value=data.get("min_value", 1.0),
            max_value=data.get("max_value", 100.0),
            step=data.get("step", 1.0),
        )

    def __repr__(self) -> str:
        return (
            f"ParameterNode(name={self.name!r}, "
            f"value={self.value}, range=[{self.min_value}, {self.max_value}])"
        )
