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
import os

from pathlib import Path
from qtpy.QtWidgets import QFileDialog, QLineEdit
from qtpy.QtCore import Signal
from typing import Optional

from core.core_enums import Alignment
from widgets.generic_dialog import GenericDialog


class DirectoryBrowser(GenericDialog):
    directory_set = Signal(str)

    def __init__(self, default_directory: Optional[Path] = None):
        super(DirectoryBrowser, self).__init__(title='Directory Browser', alignment=Alignment.horizontal)
        self.button = self.add_button('Browse...', tool_tip='Click to browse for path', event=self.browse_clicked)
        self.line_edit: QLineEdit = self.add_widget(QLineEdit())
        self.line_edit.setPlaceholderText('<enter path>')
        self.default_directory: Path = default_directory if default_directory else Path(__file__).parents[2]

    @property
    def text(self) -> str:
        return self.line_edit.text()

    def browse_clicked(self):
        d = QFileDialog.getExistingDirectory(self, 'Browse for directory', self.default_directory.as_posix(),
                                             QFileDialog.ShowDirsOnly)
        if d:
            self.line_edit.setText(d)
            self.directory_set.emit(d)


if __name__ == '__main__':
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    browser = DirectoryBrowser()
    browser.resize(600, browser.sizeHint().height())
    browser.show()
    sys.exit(app.exec())
