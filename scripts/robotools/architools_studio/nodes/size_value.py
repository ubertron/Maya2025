"""SizeValue class for representing dimension values in procedural templates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class SizeMode(Enum):
    """Mode for how a dimension value is determined."""
    constant = auto()  # Fixed numeric value
    min = auto()       # Lock to minimum of target node on this axis
    center = auto()    # Lock to center of target node on this axis
    max = auto()       # Lock to maximum of target node on this axis


@dataclass
class SizeValue:
    """Represents a dimension value (width, height, or depth).

    A dimension can be:
    - constant: A fixed numeric value
    - min/center/max: Lock to the min/center/max of a target node on this axis

    Lock modes can optionally specify a lock_node_id to lock to another meshbox
    instead of boxy (the default).

    The value field can be either:
    - A float for direct values
    - A string starting with '$' for parameter references (e.g., "$thickness")

    Attributes:
        mode: How the value is determined (constant, min, center, or max)
        value: The value when mode is constant (float or "$param_name")
        lock_node_id: Node ID to lock to (None = boxy, string = meshbox node ID)
    """
    mode: SizeMode = SizeMode.constant
    value: float | str = 0.0
    lock_node_id: str | None = None  # None means lock to boxy

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        result = {"mode": self.mode.name}

        if self.mode == SizeMode.constant:
            result["value"] = self.value
        elif self.lock_node_id:
            # Only save lock_node_id if not locking to boxy (default)
            result["lock_node_id"] = self.lock_node_id

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SizeValue":
        """Deserialize from dictionary."""
        mode_str = data.get("mode", "constant")
        mode = SizeMode[mode_str]

        return cls(
            mode=mode,
            value=data.get("value", 0.0),
            lock_node_id=data.get("lock_node_id"),
        )

    @classmethod
    def constant(cls, value: float | str) -> "SizeValue":
        """Create a constant SizeValue.

        Args:
            value: Numeric value or "$param_name" string
        """
        return cls(mode=SizeMode.constant, value=value)

    @classmethod
    def min_size(cls, lock_node_id: str | None = None) -> "SizeValue":
        """Create a SizeValue that locks to minimum of target node.

        Args:
            lock_node_id: Node to lock to (None = boxy)
        """
        return cls(mode=SizeMode.min, lock_node_id=lock_node_id)

    @classmethod
    def center_size(cls, lock_node_id: str | None = None) -> "SizeValue":
        """Create a SizeValue that locks to center of target node.

        Args:
            lock_node_id: Node to lock to (None = boxy)
        """
        return cls(mode=SizeMode.center, lock_node_id=lock_node_id)

    @classmethod
    def max_size(cls, lock_node_id: str | None = None) -> "SizeValue":
        """Create a SizeValue that locks to maximum of target node.

        Args:
            lock_node_id: Node to lock to (None = boxy)
        """
        return cls(mode=SizeMode.max, lock_node_id=lock_node_id)

    @property
    def is_lock_mode(self) -> bool:
        """True if this is a lock mode (min, center, or max)."""
        return self.mode in (SizeMode.min, SizeMode.center, SizeMode.max)

    @property
    def is_locked_to_boxy(self) -> bool:
        """True if locked to boxy (default target)."""
        return self.is_lock_mode and self.lock_node_id is None

    def is_parameter_reference(self) -> bool:
        """Check if the value references a parameter."""
        return isinstance(self.value, str) and self.value.startswith("$")

    def get_parameter_name(self) -> str | None:
        """Get the parameter name if this is a parameter reference."""
        if self.is_parameter_reference():
            return self.value[1:]  # Strip the '$' prefix
        return None

    def __repr__(self) -> str:
        if self.mode == SizeMode.constant:
            return f"SizeValue(constant={self.value})"
        else:
            target = self.lock_node_id if self.lock_node_id else "boxy"
            return f"SizeValue({self.mode.name}@{target})"
