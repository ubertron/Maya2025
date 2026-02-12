from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox


class DimensionsDialog(QDialog):
    """Modal dialog for entering Width, Height, Depth dimensions."""

    def __init__(self, parent=None, title: str = "Dimensions"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Form layout for dimension inputs
        form_layout = QFormLayout()

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.01, 10000.0)
        self.width_spin.setValue(100.0)
        self.width_spin.setDecimals(2)
        form_layout.addRow("Width:", self.width_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.01, 10000.0)
        self.height_spin.setValue(100.0)
        self.height_spin.setDecimals(2)
        form_layout.addRow("Height:", self.height_spin)

        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setRange(0.01, 10000.0)
        self.depth_spin.setValue(100.0)
        self.depth_spin.setDecimals(2)
        form_layout.addRow("Depth:", self.depth_spin)

        layout.addLayout(form_layout)

        # Button box with Create and Cancel
        button_box = QDialogButtonBox()
        self.create_button = button_box.addButton("Create", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @property
    def width(self) -> float:
        return self.width_spin.value()

    @property
    def height(self) -> float:
        return self.height_spin.value()

    @property
    def depth(self) -> float:
        return self.depth_spin.value()

    @property
    def dimensions(self) -> tuple[float, float, float]:
        return self.width, self.height, self.depth
