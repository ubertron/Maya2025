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

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QDoubleSpinBox, QCheckBox

from widgets.float_array_widget import FloatArrayWidget
from widgets.generic_widget import GenericWidget


class VectorInputWidget(GenericWidget):
    clicked = Signal()
    float_field_changed = Signal(float)

    def __init__(self, title: str, count: int = 3, default: float = 1.0, minimum: float = 0.0, maximum: float = 100.0, step: float = 0.1):
        super().__init__(title=title)
        self.field_count = count
        self.float_field: QDoubleSpinBox = self.add_widget(QDoubleSpinBox())
        self.float_field.setValue(default)
        self.float_field.setMinimum(minimum)
        self.float_field.setMaximum(maximum)
        self.float_field.setSingleStep(step)
        self.float_field.valueChanged.connect(self.float_field_changed.emit)
        self.float_array = self.add_widget(FloatArrayWidget(default_value=default, count=count, minimum=minimum, maximum=maximum))
        self.checkbox = self.add_widget(QCheckBox("Set explicit values"))
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.evaluate_fields)
        self.apply_button = self.add_button(text="Apply", clicked=self.clicked.emit)
        self.evaluate_fields()

    @property
    def value(self):
        return self.float_array.value() if self.checkbox.isChecked() else [self.float_field.value() for _ in range(self.field_count)]

    def evaluate_fields(self):
        self.float_field.setHidden(self.checkbox.isChecked())
        self.float_array.setVisible(self.checkbox.isChecked())


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = VectorInputWidget("Vector Input", count=5)
    widget.show()
    app.exec()
