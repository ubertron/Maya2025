"""
QtPy shim - PySide2/PySide6 compatibility layer.

This is a local shim that provides a unified API for PySide2 and PySide6,
allowing code to use consistent imports regardless of which Qt binding is available.

Usage:
    from qtpy.QtCore import Qt, Signal
    from qtpy.QtWidgets import QWidget, QApplication
    from qtpy.QtGui import QColor, QPixmap
"""

# Version detection flags
PYSIDE6 = False
PYSIDE2 = False
PYSIDE_VERSION = None
API_NAME = None

try:
    import PySide6
    PYSIDE6 = True
    PYSIDE_VERSION = PySide6.__version__
    API_NAME = "PySide6"
except ImportError:
    try:
        import PySide2
        PYSIDE2 = True
        PYSIDE_VERSION = PySide2.__version__
        API_NAME = "PySide2"
    except ImportError:
        raise ImportError(
            "No Qt bindings found. Install PySide2 or PySide6.\n"
            "  pip install PySide6  (for Qt6)\n"
            "  pip install PySide2  (for Qt5)"
        )

__version__ = "1.0.0"
__all__ = ["PYSIDE6", "PYSIDE2", "PYSIDE_VERSION", "API_NAME"]
