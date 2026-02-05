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
import sys

from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout
from qtpy.QtCore import QMargins


class VBoxLayout(QVBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(VBoxLayout, self).__init__()
        self.setContentsMargins(QMargins(margin, margin, margin, margin))
        self.setSpacing(spacing)


class HBoxLayout(QHBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(HBoxLayout, self).__init__()
        self.setContentsMargins(QMargins(margin, margin, margin, margin))
        self.setSpacing(spacing)


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication, QWidget, QLabel

    app = QApplication(sys.argv)
    widget = QWidget()
    widget.setLayout(VBoxLayout())
    widget.layout().addWidget(QLabel('Hello'))
    widget.show()
    app.exec()
