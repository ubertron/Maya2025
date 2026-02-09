"""QtWidgets module shim for PySide2/PySide6 compatibility."""
from qtpy import PYSIDE6

if PYSIDE6:
    from PySide6.QtWidgets import *
else:
    from PySide2.QtWidgets import *
