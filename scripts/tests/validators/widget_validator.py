"""Validator for checking if Qt architools_widgets are valid and usable."""

from __future__ import annotations

try:
    from PySide6.QtWidgets import QWidget
    import shiboken6 as shiboken
except ImportError:
    from PySide2.QtWidgets import QWidget
    import shiboken2 as shiboken


def validate_widget(widget: QWidget) -> tuple[bool, str]:
    """Validate that a widget is in a usable state.

    This function performs multiple checks to ensure a widget is valid
    and ready to be reused, rather than being a "zombie" instance that
    exists in memory but has been closed or deleted.

    Args:
        widget: The QWidget to validate

    Returns:
        A tuple of (is_valid, reason) where:
        - is_valid: True if the widget passes all validation checks
        - reason: Empty string if valid, otherwise a description of why validation failed

    Example:
        is_valid, reason = validate_widget(my_widget)
        if not is_valid:
            print(f"Widget validation failed: {reason}")
    """
    # Check 1: Widget exists in C++ memory
    if not shiboken.isValid(widget):
        return False, "shiboken.isValid() = False (C++ object deleted)"

    # Check 2: Widget has a valid layout with children (not a cleared zombie widget)
    layout = widget.layout()
    if layout is None:
        return False, "widget.layout() is None (no layout)"

    layout_count = layout.count()
    if layout_count == 0:
        return False, f"layout.count() = 0 (empty layout)"

    # Check 3: Window handle is valid (not closed)
    # Note: This check is not always reliable on Windows, where window handles
    # may persist even after closing
    if widget.windowHandle() is None:
        return False, "windowHandle() is None (window closed)"

    # Check 4: Widget is not hidden (was closed by user)
    # This is the most reliable check for Windows zombie architools_widgets
    if widget.isHidden():
        return False, "widget is hidden (closed by user)"

    # All checks passed
    return True, ""
