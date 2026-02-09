"""Shiboken module shim for PySide2/PySide6 compatibility."""
from qtpy import PYSIDE6

if PYSIDE6:
    from shiboken6 import *
else:
    from shiboken2 import *
