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
