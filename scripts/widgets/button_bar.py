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

import sys

from qtpy.QtWidgets import QSizePolicy

from core.core_enums import Alignment
from core.core_paths import image_path
from widgets.generic_widget import GenericWidget
from widgets.icon_button import IconButton


class ButtonBar(GenericWidget):
    """Horizontal container for buttons."""

    def __init__(self, title: str = "", button_size: int = 32):
        super().__init__(title = title, alignment=Alignment.horizontal)
        self.button_size = button_size
        self.setFixedHeight(self.sizeHint().height() + button_size)

    def add_icon_button(self, icon_path: Path | None, tool_tip: str = "", size: int | None = None, margin: int = 2,
                        clicked: Callable | None = None) -> IconButton:
        """Add an icon button to the layout."""
        icon_path = icon_path if icon_path is not None else image_path("script.png")
        icon_button = IconButton(icon_path=icon_path, tool_tip=tool_tip, size=size if size else self.button_size,
                                 margin=margin, clicked=clicked)
        self.add_widget(widget=icon_button)
        return icon_button


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    from pathlib import Path

    app = QApplication(sys.argv)
    widget = ButtonBar("Test Button Bar")
    widget.add_icon_button(Path.home().joinpath("Dropbox/Technology/Python3/Projects/Maya2025/images/icons/add.png"))
    widget.add_stretch()
    # widget.setFixedWidth(200)
    widget.show()
    sys.exit(app.exec())
