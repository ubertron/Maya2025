"""ArchitypeTemplate class - root container for procedural templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from robotools.architools_studio.nodes.base_node import BaseNode, create_node_from_dict
from robotools.architools_studio.nodes.meshbox_node import MeshBoxNode


@dataclass
class ArchitypeTemplate:
    """Root container for an architype definition.

    An ArchitypeTemplate contains all the nodes and metadata needed to
    procedurally generate an architectural object relative to a Boxy node.

    Attributes:
        name: Template name (becomes tab name in Architools)
        version: Template schema version
        description: Optional description of the template
        tags: List of descriptive tags for organization
        boxy_node_name: Name of the linked Maya Boxy node (live reference)
        nodes: Dictionary mapping node IDs to node instances
        root_node_ids: IDs of top-level MeshBoxNodes (no parent)
        parameters: List of parameter definitions (Phase 7)
    """
    name: str = "untitled"
    version: str = "1.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    boxy_node_name: str | None = None
    nodes: dict[str, BaseNode] = field(default_factory=dict)
    root_node_ids: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)

    def add_node(self, node: BaseNode) -> str:
        """Add a node to the template.

        Args:
            node: The node to add

        Returns:
            The node's ID
        """
        self.nodes[node.id] = node
        if node.parent_id is None and isinstance(node, MeshBoxNode):
            if node.id not in self.root_node_ids:
                self.root_node_ids.append(node.id)
        return node.id

    def remove_node(self, node_id: str) -> BaseNode | None:
        """Remove a node from the template.

        Also removes from root_node_ids if applicable and removes
        the node ID from any parent's children list.

        Args:
            node_id: ID of the node to remove

        Returns:
            The removed node, or None if not found
        """
        node = self.nodes.pop(node_id, None)
        if node is None:
            return None

        # Remove from root_node_ids
        if node_id in self.root_node_ids:
            self.root_node_ids.remove(node_id)

        # Remove from parent's children list
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if isinstance(parent, MeshBoxNode) and node_id in parent.children:
                parent.children.remove(node_id)

        return node

    def get_node(self, node_id: str) -> BaseNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> list[BaseNode]:
        """Get all child nodes of a given node.

        Args:
            node_id: ID of the parent node

        Returns:
            List of child nodes
        """
        return [n for n in self.nodes.values() if n.parent_id == node_id]

    def get_root_nodes(self) -> list[MeshBoxNode]:
        """Get all root-level MeshBox nodes."""
        return [
            self.nodes[node_id]
            for node_id in self.root_node_ids
            if node_id in self.nodes
        ]

    def get_all_meshbox_nodes(self) -> list[MeshBoxNode]:
        """Get all MeshBox nodes in the template."""
        return [n for n in self.nodes.values() if isinstance(n, MeshBoxNode)]

    def get_all_parameter_nodes(self) -> list:
        """Get all ParameterNode instances in the template."""
        from robotools.architools_studio.nodes.parameter_node import ParameterNode
        return [n for n in self.nodes.values() if isinstance(n, ParameterNode)]

    def get_parameter_by_name(self, name: str):
        """Get a ParameterNode by its name.

        Args:
            name: Parameter name (without $ prefix)

        Returns:
            ParameterNode or None if not found
        """
        from robotools.architools_studio.nodes.parameter_node import ParameterNode
        for node in self.nodes.values():
            if isinstance(node, ParameterNode) and node.name == name:
                return node
        return None

    def get_parameter_value(self, name: str, default: float = 0.0) -> float:
        """Get the current value of a parameter by name.

        Args:
            name: Parameter name (without $ prefix)
            default: Default value if parameter not found

        Returns:
            Current parameter value or default
        """
        param = self.get_parameter_by_name(name)
        return param.value if param else default

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tags": self.tags.copy(),
            "parameters": [p.copy() for p in self.parameters],
            "nodes": [node.to_dict() for node in self.nodes.values()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchitypeTemplate":
        """Deserialize from dictionary."""
        template = cls(
            name=data.get("name", "untitled"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            parameters=data.get("parameters", []),
        )

        # Deserialize nodes
        for node_data in data.get("nodes", []):
            node = create_node_from_dict(node_data)
            template.add_node(node)

        return template

    def validate(self) -> list[str]:
        """Validate the template and return a list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check for required name
        if not self.name or self.name == "untitled":
            issues.append("Template must have a name")

        # Check for at least one meshbox
        if not self.root_node_ids:
            issues.append("Template must have at least one MeshBox node")

        # Check for orphaned children
        for node in self.nodes.values():
            if node.parent_id and node.parent_id not in self.nodes:
                issues.append(f"Node '{node.name}' references missing parent '{node.parent_id}'")

        # Check for missing children
        for node in self.nodes.values():
            if isinstance(node, MeshBoxNode):
                for child_id in node.children:
                    if child_id not in self.nodes:
                        issues.append(f"Node '{node.name}' references missing child '{child_id}'")

        # Check parameter references
        all_param_names = {p.get("name") for p in self.parameters}
        for node in self.nodes.values():
            if isinstance(node, MeshBoxNode):
                for param_name in node.get_parameter_references():
                    if param_name not in all_param_names:
                        issues.append(f"Node '{node.name}' references undefined parameter '${param_name}'")

        return issues

    def clear(self) -> None:
        """Clear all nodes from the template."""
        self.nodes.clear()
        self.root_node_ids.clear()

    def __len__(self) -> int:
        """Return the number of nodes in the template."""
        return len(self.nodes)

    def __repr__(self) -> str:
        return (
            f"ArchitypeTemplate(name={self.name!r}, "
            f"nodes={len(self.nodes)}, "
            f"params={len(self.parameters)})"
        )
