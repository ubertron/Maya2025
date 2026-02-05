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

Widget to use for help documentation.
"""
from __future__ import annotations

from qtpy.QtWidgets import QLabel, QWidget

from core.core_enums import Side
from widgets.generic_widget import GenericWidget


class HelpWidget(GenericWidget):
    """Class for help."""

    def __init__(self, title: str, parent_widget: QWidget) -> None:
        """Init."""
        super().__init__(title=title)
        self.parent_widget = parent_widget

    def add_section(self, title: str, body: str | QWidget) -> QWidget:
        """Add a section with a title and body content in a group box.

        Args:
            title: The section title (displayed as group box title).
            body: Either a string (converted to QLabel) or a QWidget.

        Returns:
            The body widget.
        """
        if isinstance(body, str):
            widget = QLabel(body)
            widget.setWordWrap(True)
        else:
            widget = body

        widget.setWindowTitle(title)
        return self.add_group_box(widget=widget)

    def add_title(self, text: str) -> QLabel:
        """Add a title label."""
        label: QLabel = self.add_label(text=f"<b>{text}</b>", side=Side.left)
        return label

    def add_text_block(self, title: str, text: str) -> QLabel:
        """Add a text block to the widget."""
        self.add_title(text=title)
        return self.add_label(text=text, side=Side.left)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    widget = HelpWidget(title="Test Help", parent_widget=None)
    widget.add_section(title="Test Section", body="This is the body text for the test section.")
    widget.show()
    app.exec()
