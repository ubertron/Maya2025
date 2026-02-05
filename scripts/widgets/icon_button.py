"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Custom Qt widget library
   - Related UI components and templates
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

from qtpy.QtWidgets import QApplication, QPushButton
from qtpy.QtCore import QSize, Signal
from qtpy.QtGui import QPixmap, QIcon
from typing import Callable

from core.core_paths import image_path


class Icon(QIcon):
    def __init__(self, icon_path: str):
        super(Icon, self).__init__(QPixmap(icon_path))
        self.path = icon_path


class IconButton(QPushButton):
    checked = Signal(bool)

    def __init__(self, icon_path: Path, tool_tip: str = "", size: int = 40, margin: int = 2, clicked: Callable | None = None) -> None:
        """
        Creates a square button using an image file
        :param icon_path:
        :param size:
        :param text: optional text accompaniment
        """
        assert icon_path is not None, f"Icon path invalid: {icon_path}"
        super(IconButton, self).__init__()
        self.setToolTip(tool_tip if tool_tip else icon_path.stem)
        if icon_path.exists():
            self.setToolTip(tool_tip)
            self.setIcon(QIcon(QPixmap(str(icon_path))))
            self.setIconSize(QSize(size, size))
            self.setFixedSize(QSize(size + margin * 2, size + margin * 2))
        else:
            self.setFixedHeight(size)
            self.setStyleSheet("Text-align:center")
        if clicked:
            self.clicked.connect(clicked)



if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    from core.core_paths import image_path

    import qdarktheme
    app = QApplication(sys.argv)
    widget = IconButton(icon_path=image_path("file.png"), size=128)
    widget.show()
    app.exec()