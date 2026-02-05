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
import enum

from qtpy import PYSIDE6
from qtpy.QtWidgets import QLabel
from qtpy.QtCore import QPoint, Qt, Signal
from qtpy.QtGui import QMouseEvent
from widgets.generic_widget import GenericWidget


class ClickableLabel(QLabel):
    clicked: Signal = Signal(QPoint)
    clicked_right: Signal = Signal(QPoint)

    def __init__(self, *args, global_context: bool = True, button: enum = Qt.MouseButton.LeftButton):
        super(ClickableLabel, self).__init__(*args)
        assert type(button).__name__ == 'MouseButton', 'Please supply Qt.MouseButton enum'
        self.global_context: bool = global_context
        self.button: enum = button

    def mousePressEvent(self, event):
        # PySide2/6 compatibility: globalPos() vs globalPosition()
        if PYSIDE6:
            global_position = event.globalPosition().toPoint()
        else:
            global_position = event.globalPos()

        local_position = self.window().mapFromGlobal(global_position)
        position = global_position if self.global_context else local_position

        if event.button() == Qt.MouseButton.RightButton:
            self.clicked_right.emit(position)
        elif event.button() == self.button:
            self.clicked.emit(position)


class TestWidget(GenericWidget):
    def __init__(self):
        super(TestWidget, self).__init__('Clickable Label Test Widget')
        label = self.add_widget(ClickableLabel('This is a label', global_context=False))
        self.resize(320, 40)
        label.clicked.connect(self.label_clicked)

    @staticmethod
    def label_clicked(args):
        print(f'Label clicked: {args}')


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    widget = TestWidget()
    widget.show()
    app.exec()
