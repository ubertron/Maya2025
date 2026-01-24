"""Utilities for launching and managing Maya widgets."""

from __future__ import annotations

import importlib

from typing import Any
try:
    from PySide6.QtWidgets import QWidget
    import shiboken6 as shiboken
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import QWidget
    import shiboken2 as shiboken
    PYSIDE_VERSION = 2

from maya_tools.maya_environment_utils import MAYA_MAIN_WINDOW
from tests.validators import widget_validator


def launch_tool(
    tool_module: str,
    tool_class: str,
    use_workspace_control: bool = False,
    ui_script: str = "",
    reload_module: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> QWidget:
    """Launch a Maya tool with singleton instance management.

    This function checks for existing instances of a tool before creating a new one.
    If an instance exists, it will be shown and brought to the front. If no instance
    exists, a new one will be created and displayed.

    Args:
        tool_module: Module path to import (e.g., "python.metadata.asset_resolution_tool")
        tool_class: Class name to instantiate (e.g., "AssetResolutionTool")
        use_workspace_control: If True, use show_workspace_control() for dockable window,
            else use show() for simple floating window. Defaults to False.
        ui_script: UI script for workspace control restoration. Only used if
            use_workspace_control=True. Defaults to empty string.
        reload_module: If True, reload the module before instantiating. Useful during
            development when module code has changed. Defaults to False.
        debug: If True, print diagnostic information during launch. Defaults to False.
        **kwargs: Keyword arguments to pass to the tool class constructor

    Returns:
        The widget instance (either existing or newly created)

    Example:
        # Simple floating window
        tool = launch_tool("python.metadata.asset_resolution_tool", "AssetResolutionTool")

        # With workspace control
        tool = launch_tool(
            "utils.maya.vray_material_tool",
            "VrayMaterialTool",
            use_workspace_control=True,
            ui_script="from maya_tools import vray_material_tool; "
                     "vray_material_tool.VrayMaterialTool().restore()"
        )

        # With initialization kwargs and module reload
        tool = maya_widget_utils.launch_tool(
            tool_module="widgets.generic_widget",
            tool_class="ExampleGenericWidget",
            reload_module=True
        )
    """
    # Import the module
    module = importlib.import_module(tool_module)

    # Reload if requested (useful during development)
    if reload_module:
        module = importlib.reload(module)

    # Get the class from the module
    class_type = getattr(module, tool_class)

    if debug:
        print(f"\n=== LAUNCH_TOOL DEBUG: {tool_class} ===")
        print(f"Module: {tool_module}")
        print(f"Class type: {class_type}")
        print(f"File: {__file__}")
        import datetime
        print(f"Loaded at: {datetime.datetime.now()}")

    # Search for existing instances
    existing_instance = None
    candidates = []
    for widget in MAYA_MAIN_WINDOW.findChildren(QWidget):
        # Check if this widget is an instance of the tool class
        # When reloading, check only by name since isinstance() will fail
        # (old instances are from the old class definition)
        class_name_matches = type(widget).__name__ == tool_class
        if reload_module:
            # During reload, only check class name (will find old class instances)
            if not class_name_matches:
                continue
            # Close old instances when reloading to use fresh code
            if debug:
                print(f"  Found old instance {id(widget)} from before reload - will close and create fresh")
            try:
                widget.close()
                widget.deleteLater()
            except Exception:
                pass
            continue
        else:
            # Normal mode: strict check with isinstance
            if not (class_name_matches and isinstance(widget, class_type)):
                continue
            candidates.append(widget)
            # Verify the widget is still valid and usable
            is_valid, reason = widget_validator.validate_widget(widget)

            if debug:
                print(f"\n  Checking candidate {id(widget)}:")
                print(f"    isValid: {shiboken.isValid(widget)}")
                print(f"    isVisible: {widget.isVisible()}")
                print(f"    isHidden: {widget.isHidden()}")
                print(f"    windowHandle: {widget.windowHandle()}")
                print(f"    layout: {widget.layout()}")
                print(f"    layout.count: {widget.layout().count() if widget.layout() else 'N/A'}")
                print(f"    validation: {'PASS' if is_valid else f'FAIL - {reason}'}")

            if not is_valid:
                if debug:
                    print(f"  Candidate {id(widget)}: REJECTED - {reason}")
                continue

            # Widget is valid and populated, use it
            if debug:
                layout_count = widget.layout().count() if widget.layout() else 0
                print(f"  Candidate {id(widget)}: ACCEPTED - valid with {layout_count} children")
            existing_instance = widget
            break

    if debug:
        print(f"Total candidates found: {len(candidates)}")
        print(f"Existing instance selected: {existing_instance is not None}")

    # If instance found, show and raise it
    if existing_instance is not None:
        if debug:
            print(f"Showing existing instance {id(existing_instance)}")
        existing_instance.show()
        existing_instance.raise_()
        existing_instance.activateWindow()
        return existing_instance

    if debug:
        print(f"Creating new instance with kwargs: {kwargs}")

    # No instance found, create a new one
    instance = class_type(**kwargs)

    # Display the widget based on the chosen method
    if use_workspace_control:
        instance.show_workspace_control(ui_script=ui_script)
    else:
        instance.show()

    return instance


def print_widget_diagnostics(widget: QWidget) -> None:
    """Print diagnostic information about a widget's state.

    Useful for debugging widget lifecycle issues, especially on Windows
    where closed widgets may become "zombie" instances.

    Args:
        widget: The widget to diagnose
    """
    print("=" * 60)
    print("WIDGET DIAGNOSTICS")
    print("=" * 60)

    # Basic validity
    print(f"Widget type: {type(widget)}")
    print(f"Widget class name: {type(widget).__name__}")
    print(f"Shiboken valid: {shiboken.isValid(widget)}")
    print(f"Widget visible: {widget.isVisible()}")
    print(f"Widget hidden: {widget.isHidden()}")

    # Layout info
    layout = widget.layout()
    print(f"\nLayout exists: {layout is not None}")
    if layout:
        print(f"Layout type: {type(layout)}")
        print(f"Layout count: {layout.count()}")
        print(f"Layout children:")
        for i in range(layout.count()):
            item = layout.itemAt(i)
            child_widget = item.widget() if item else None
            is_valid = shiboken.isValid(child_widget) if child_widget else False
            print(f"  [{i}] {child_widget} - Valid: {is_valid if child_widget else 'N/A'}")

    # Check all children recursively
    all_children = widget.findChildren(QWidget)
    print(f"\nTotal child widgets: {len(all_children)}")
    print(f"Valid children: {sum(1 for w in all_children if shiboken.isValid(w))}")

    # Object ID (to see if it's reusing same instance)
    print(f"\nPython object ID: {id(widget)}")

    # Validation status
    is_valid, reason = widget_validator.validate_widget(widget)
    print(f"\nValidation: {'PASS' if is_valid else f'FAIL'}")
    if not is_valid:
        print(f"Failure reason: {reason}")

    print("=" * 60)
