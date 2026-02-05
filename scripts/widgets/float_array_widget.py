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

from qtpy.QtWidgets import QWidget, QDoubleSpinBox, QHBoxLayout, QLabel
from qtpy.QtCore import Signal
from scipy.interpolate.dfitpack import splint


class FloatArrayWidget(QWidget):
    value_changed = Signal()

    def __init__(self, count: int = 3, default_value: float =0.0, minimum: float = 0.0, maximum: float = 1.0, step: float = 0.1):
        super(FloatArrayWidget, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for i in range(count):
            spinbox = QDoubleSpinBox()
            spinbox.setValue(default_value)
            spinbox.setMinimum(minimum)
            spinbox.setMaximum(maximum)
            spinbox.valueChanged.connect(self.value_changed_event)
            spinbox.setSingleStep(step)
            layout.addWidget(spinbox)
        self.setLayout(layout)

    @property
    def widgets(self) -> list[QDoubleSpinBox]:
        return [self.layout().itemAt(i).widget() for i in range(self.layout().count())]

    @property
    def values(self) -> list[float]:
        return [x.value() for x in self.widgets]

    def value_changed_event(self):
        self.value_changed.emit()


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = FloatArrayWidget()
    widget.show()
    print(widget.values)
    app.exec()
