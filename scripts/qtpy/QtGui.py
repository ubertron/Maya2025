"""QtGui module shim for PySide2/PySide6 compatibility.

Handles classes that moved between QtWidgets and QtGui across PySide versions:
- QAction: QtWidgets (PySide2) -> QtGui (PySide6)
- QShortcut: QtWidgets (PySide2) -> QtGui (PySide6)
- QUndoCommand: QtWidgets (PySide2) -> QtGui (PySide6)
"""
from qtpy import PYSIDE6

if PYSIDE6:
    from PySide6.QtGui import *
else:
    from PySide2.QtGui import *
    # Import classes that are in QtWidgets in PySide2 but QtGui in PySide6
    # This allows code written for PySide6 to work with PySide2
    try:
        from PySide2.QtWidgets import QAction, QShortcut, QUndoCommand
    except ImportError:
        pass
