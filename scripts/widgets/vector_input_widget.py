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
