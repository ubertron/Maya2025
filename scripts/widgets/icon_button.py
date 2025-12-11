from __future__ import annotations
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QPixmap, QIcon
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
            self.setIcon(QIcon(QPixmap(icon_path)))
            self.setIconSize(QSize(size, size))
            self.setFixedSize(QSize(size + margin * 2, size + margin * 2))
        else:
            self.setFixedHeight(size)
            self.setStyleSheet("Text-align:center")
        if clicked:
            self.clicked.connect(clicked)



if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from core.core_paths import image_path

    import qdarktheme
    app = QApplication(sys.argv)
    widget = IconButton(icon_path=image_path("file.png"), size=128)
    widget.show()
    app.exec()