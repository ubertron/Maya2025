"""JSON save/load utilities for ArchitoolsStudio templates."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robotools.architools_studio.nodes.architype_template import ArchitypeTemplate


# Default location for architype template files
ARCHITYPES_FOLDER = Path(__file__).parent.parent / "architools" / "data" / "architypes"


def get_architypes_folder() -> Path:
    """Get the path to the architypes data folder.

    Creates the folder if it doesn't exist.

    Returns:
        Path to the architypes folder
    """
    folder = ARCHITYPES_FOLDER
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_template(template: "ArchitypeTemplate", filepath: str | Path | None = None) -> Path:
    """Save a template to a JSON file.

    Args:
        template: The ArchitypeTemplate to save
        filepath: Optional path to save to. If None, saves to the default
                  architypes folder using the template name.

    Returns:
        Path to the saved file

    Raises:
        ValueError: If template has no name
        OSError: If file cannot be written
    """
    from robotools.architools_studio.nodes.architype_template import ArchitypeTemplate

    if not template.name or template.name == "untitled":
        raise ValueError("Template must have a name before saving")

    if filepath is None:
        # Generate filename from template name
        filename = f"{template.name}.json"
        filepath = get_architypes_folder() / filename
    else:
        filepath = Path(filepath)

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Serialize and save
    data = template.to_dict()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_template(filepath: str | Path) -> "ArchitypeTemplate":
    """Load a template from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        ArchitypeTemplate instance

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If file doesn't contain valid template data
    """
    from robotools.architools_studio.nodes.architype_template import ArchitypeTemplate

    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Template file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid template data in {filepath}")

    return ArchitypeTemplate.from_dict(data)


def load_template_by_name(name: str) -> "ArchitypeTemplate":
    """Load a template by name from the default architypes folder.

    Args:
        name: Template name (without .json extension)

    Returns:
        ArchitypeTemplate instance

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    filepath = get_architypes_folder() / f"{name}.json"
    return load_template(filepath)


def list_templates() -> list[str]:
    """List all available template names in the architypes folder.

    Returns:
        List of template names (without .json extension)
    """
    folder = get_architypes_folder()
    templates = []

    for filepath in folder.glob("*.json"):
        templates.append(filepath.stem)

    return sorted(templates)


def delete_template(name: str) -> bool:
    """Delete a template file by name.

    Args:
        name: Template name (without .json extension)

    Returns:
        True if deleted, False if file didn't exist
    """
    filepath = get_architypes_folder() / f"{name}.json"

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def template_exists(name: str) -> bool:
    """Check if a template exists.

    Args:
        name: Template name (without .json extension)

    Returns:
        True if template file exists
    """
    filepath = get_architypes_folder() / f"{name}.json"
    return filepath.exists()


def validate_template_file(filepath: str | Path) -> list[str]:
    """Validate a template file without fully loading it.

    Args:
        filepath: Path to the JSON file

    Returns:
        List of validation errors (empty if valid)
    """
    filepath = Path(filepath)
    errors = []

    if not filepath.exists():
        errors.append(f"File not found: {filepath}")
        return errors

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append("Root element must be an object")
        return errors

    # Check required fields
    if "name" not in data:
        errors.append("Missing required field: name")

    if "nodes" not in data:
        errors.append("Missing required field: nodes")
    elif not isinstance(data["nodes"], list):
        errors.append("Field 'nodes' must be an array")

    # Check nodes have required fields
    for i, node in enumerate(data.get("nodes", [])):
        if not isinstance(node, dict):
            errors.append(f"Node {i} must be an object")
            continue
        if "id" not in node:
            errors.append(f"Node {i} missing required field: id")
        if "type" not in node:
            errors.append(f"Node {i} missing required field: type")
        if "name" not in node:
            errors.append(f"Node {i} missing required field: name")

    return errors
