"""
Boxy Geometry Validator

Validates that a node is a proper boxy object (boxyShape).

Usage:
    from tests.validators.boxy_validator import validator_boxy
    import logging

    # Basic validation
    result, issues = validator_boxy(node="boxy1")
    if result:
        print("Valid boxy object")
    else:
        print("Invalid boxy object")
        print("\\n".join(issues))
"""

import logging
import maya.cmds as cmds

from core.logging_utils import get_logger

# Initialize logger
LOGGER = get_logger(name=__name__, level=logging.INFO)


def validator_boxy(node: str, test_poly_cube: bool = False):
    """
    Validate that a node is a proper boxy object (boxyShape).

    Args:
        node (str): Name of the object to validate
        test_poly_cube (bool): Unused, kept for backward compatibility

    Returns:
        tuple: (bool, list)
            - bool: True if all validations pass, False otherwise
            - list: List of validation error messages (empty if passed)

    Example:
        result, issues = validator_boxy(node="boxy1")
        if not result:
            for issue in issues:
                print(f"  - {issue}")
    """
    # Check if node exists
    if not cmds.objExists(node):
        return False, [f"Node '{node}' does not exist"]

    # Check if this is a boxyShape
    shapes = cmds.listRelatives(node, shapes=True)
    if not shapes or cmds.objectType(shapes[0]) != "boxyShape":
        return False, [f"Node '{node}' is not a boxy node (expected boxyShape)"]

    return _validate_boxy_shape(node, shapes[0])


def _validate_boxy_shape(transform: str, shape: str):
    """
    Validate a boxy node (boxyShape).

    Args:
        transform (str): Transform node name
        shape (str): Shape node name (boxyShape)

    Returns:
        tuple: (bool, list) - (passed, issues)
    """
    issues = []

    # Check for customType attribute on shape
    if not cmds.attributeQuery('customType', node=shape, exists=True):
        issues.append(f"Shape '{shape}' does not have required 'customType' attribute")
    else:
        try:
            custom_type_value = cmds.getAttr(f'{shape}.customType')
            if custom_type_value != "boxy":
                issues.append(f"Attribute 'customType' must be 'boxy', found '{custom_type_value}'")
        except Exception as e:
            issues.append(f"Failed to read 'customType' attribute: {str(e)}")

    # Check for pivot attribute on shape
    if not cmds.attributeQuery('pivot', node=shape, exists=True):
        issues.append(f"Shape '{shape}' does not have required 'pivot' attribute")

    # Check for size attributes on shape
    for attr in ['sizeX', 'sizeY', 'sizeZ']:
        if not cmds.attributeQuery(attr, node=shape, exists=True):
            issues.append(f"Shape '{shape}' does not have required '{attr}' attribute")

    # Check for wireframeColor attributes on shape
    for attr in ['wireframeColorR', 'wireframeColorG', 'wireframeColorB']:
        if not cmds.attributeQuery(attr, node=shape, exists=True):
            issues.append(f"Shape '{shape}' does not have required '{attr}' attribute")

    passed = len(issues) == 0
    return passed, issues


def test_selected_boxy(node=None, test_poly_cube: bool = False):
    """
    Test a boxy node (boxyShape).

    Args:
        node (str, optional): Name of the object to test. If None, uses current selection.
                             Must be a single node name (string), not a list.
        test_poly_cube (bool): Unused, kept for backward compatibility.

    Returns:
        tuple: (bool, list) - (passed, issues)

    Logging:
        By default, only pass/fail results are logged (INFO level).
        To see detailed validation issues, set logger to DEBUG level:
            logger.setLevel(logging.DEBUG)
        To disable all output:
            logger.setLevel(logging.WARNING)

    For quick testing in Maya script editor.
    """
    # Validate input
    if node is not None:
        # Check that a string was passed, not a list or other type
        if not isinstance(node, str):
            LOGGER.error("node argument must be a single string, not a list or other type")
            LOGGER.debug(f"Received: {type(node).__name__}")
            return False, ["node argument must be a single string"]
    else:
        # Use selection if no node specified
        selected = cmds.ls(selection=True)

        if not selected:
            LOGGER.error("Please select an object first or provide a node name!")
            return False, ["No object selected or specified"]

        if len(selected) > 1:
            LOGGER.error(f"Multiple objects selected ({len(selected)}). Please select only one object.")
            LOGGER.debug(f"Selected: {', '.join(selected)}")
            return False, [f"Multiple objects selected: {', '.join(selected)}. Only one allowed."]

        node = selected[0]

    LOGGER.debug(f"\n{'=' * 60}")
    LOGGER.debug(f"Validating Boxy Geometry: {node}")
    LOGGER.debug('=' * 60)

    result, issues = validator_boxy(node, test_poly_cube=test_poly_cube)

    if result:
        LOGGER.debug(f"✅ PASSED: Object '{node}' is a valid boxy node")
    else:
        LOGGER.info(f"❌ FAILED: Object '{node}' is not a valid boxy node")
        LOGGER.debug("\nIssues found:")
        for issue in issues:
            LOGGER.debug(f"  • {issue}")

    LOGGER.debug('=' * 60 + '\n')

    return result, issues


if __name__ == '__main__':
    # When run directly in Maya, test selected object
    test_selected_boxy()