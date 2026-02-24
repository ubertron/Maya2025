"""Base node class for ArchitoolsStudio procedural templates."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseNode(ABC):
    """Abstract base class for all architype nodes.

    Attributes:
        id: Unique identifier (UUID string)
        name: Display name for the node
        parent_id: Parent node ID, or None for root-level nodes
    """
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None

    @property
    @abstractmethod
    def node_type(self) -> str:
        """Return the node type identifier for serialization."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize node to dictionary for JSON export.

        Subclasses should call super().to_dict() and extend the result.
        """
        return {
            "id": self.id,
            "type": self.node_type,
            "name": self.name,
            "parent_id": self.parent_id,
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseNode":
        """Deserialize node from dictionary.

        Subclasses should implement their own from_dict method.
        """
        raise NotImplementedError


def create_node_from_dict(data: dict[str, Any]) -> BaseNode:
    """Factory function to create the appropriate node type from a dictionary.

    Args:
        data: Dictionary containing node data with a 'type' field

    Returns:
        Appropriate BaseNode subclass instance

    Raises:
        ValueError: If the node type is unknown
    """
    from robotools.architools_studio.nodes.meshbox_node import MeshBoxNode
    from robotools.architools_studio.nodes.offset_node import OffsetNode
    from robotools.architools_studio.nodes.mirror_node import MirrorNode
    from robotools.architools_studio.nodes.parameter_node import ParameterNode

    node_type = data.get("type")

    type_mapping = {
        "meshbox": MeshBoxNode,
        "offset": OffsetNode,
        "mirror": MirrorNode,
        "parameter": ParameterNode,
    }

    node_class = type_mapping.get(node_type)
    if node_class is None:
        raise ValueError(f"Unknown node type: {node_type}")

    return node_class.from_dict(data)
