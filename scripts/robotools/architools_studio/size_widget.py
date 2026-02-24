import sys

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLineEdit, QDoubleSpinBox, QSizePolicy, QComboBox, QLabel

from core.core_enums import Alignment
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.radio_button_widget import RadioButtonWidget


class MinCenterMaxPicker(RadioButtonWidget):
    def __init__(self, title: str, default_id: int = 2):
        super().__init__(
            title=title,
            button_text_list=("Minimum", "Center", "Maximum"),
            active_id=default_id,  # Default to Maximum (2)
        )


class SizeWidget(GenericWidget):
    default_value: float = 50.0
    value_changed = Signal()
    mode_changed = Signal()  # Emitted when any row's mode changes

    def __init__(self):
        super().__init__(title="Size Widget")
        self.width_row: SizeRowWidget = self.add_widget(widget=SizeRowWidget(title="Width"))
        self.height_row: SizeRowWidget = self.add_widget(widget=SizeRowWidget(title="Height"))
        self.depth_row: SizeRowWidget = self.add_widget(widget=SizeRowWidget(title="Depth"))
        self._setup_ui()

    def _setup_ui(self):
        """Connect signals."""
        self.width_row.value_changed.connect(self.value_changed.emit)
        self.height_row.value_changed.connect(self.value_changed.emit)
        self.depth_row.value_changed.connect(self.value_changed.emit)
        self.width_row.mode_changed.connect(self.mode_changed.emit)
        self.height_row.mode_changed.connect(self.mode_changed.emit)
        self.depth_row.mode_changed.connect(self.mode_changed.emit)

    @property
    def values(self) -> tuple[float, float, float]:
        """Get current values as tuple."""
        return (
            self.width_row.value,
            self.height_row.value,
            self.depth_row.value,
        )

    def set_values(self, width: float, height: float, depth: float):
        """Set all values."""
        self.width_row.value = width
        self.height_row.value = height
        self.depth_row.value = depth

    def set_available_nodes(self, nodes: list[tuple[str, str]], exclude_id: str | None = None):
        """Set available nodes for linking on all rows.

        Args:
            nodes: List of (node_id, node_name) tuples.
            exclude_id: Node ID to exclude (typically the current node).
        """
        self.width_row.set_available_nodes(nodes, exclude_id)
        self.height_row.set_available_nodes(nodes, exclude_id)
        self.depth_row.set_available_nodes(nodes, exclude_id)


class SizeRowWidget(GenericWidget):
    """Widget for editing a single dimension (width, height, or depth).

    Lock mode: Lock to a node's min/center/max on this axis (default: boxy)
    Constant mode: Fixed numeric value
    """
    value_changed = Signal()
    mode_changed = Signal()  # Emitted when Lock/Constant or lock options change

    # Mode indices
    MODE_LOCK = 0
    MODE_CONSTANT = 1

    # Special ID for boxy node in combo
    BOXY_ID = "__boxy__"

    def __init__(self, title: str):
        super().__init__(alignment=Alignment.horizontal)
        self._title = title
        self.radio_button_widget: RadioButtonWidget = self.add_widget(
            widget=RadioButtonWidget(title=title, button_text_list=("Lock", "Constant"), active_id=0))
        self.lock_picker: MinCenterMaxPicker = self.add_widget(MinCenterMaxPicker(title=f"{title} Lock"))

        # Node selector for Lock mode (which node to lock to)
        self.lock_node_combo: QComboBox = self.add_widget(QComboBox())
        self.lock_node_combo.setMinimumWidth(100)
        self.lock_node_combo.addItem("Boxy", self.BOXY_ID)  # Default option

        self.spin_box: QDoubleSpinBox = self.add_widget(QDoubleSpinBox())
        self.spin_box.setRange(0.0, 10000.0)
        self.spin_box.setValue(50.0)

        self._setup_ui()

    def _setup_ui(self):
        self.radio_button_widget.clicked.connect(self._on_mode_changed)
        self.radio_button_widget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred))
        self.lock_picker.clicked.connect(self._on_lock_option_changed)
        self.lock_node_combo.currentIndexChanged.connect(self._on_lock_option_changed)
        self.spin_box.valueChanged.connect(lambda _: self.value_changed.emit())
        self.update_ui()

    def _on_mode_changed(self):
        """Handle Lock/Constant toggle."""
        self.update_ui()
        self.mode_changed.emit()

    def _on_lock_option_changed(self):
        """Handle Min/Center/Max or node selection change."""
        self.mode_changed.emit()

    def update_ui(self):
        mode_id = self.radio_button_widget.current_button_id
        is_lock = mode_id == self.MODE_LOCK
        self.lock_picker.setVisible(is_lock)
        self.lock_node_combo.setVisible(is_lock)
        self.spin_box.setVisible(mode_id == self.MODE_CONSTANT)

    @property
    def value(self) -> float:
        """Get the current constant value."""
        return self.spin_box.value()

    @value.setter
    def value(self, val: float):
        """Set the constant value."""
        self.spin_box.blockSignals(True)
        self.spin_box.setValue(val)
        self.spin_box.blockSignals(False)

    @property
    def is_lock_mode(self) -> bool:
        """True if in Lock mode."""
        return self.radio_button_widget.current_button_id == self.MODE_LOCK

    @property
    def is_constant_mode(self) -> bool:
        """True if in Constant mode."""
        return self.radio_button_widget.current_button_id == self.MODE_CONSTANT

    @property
    def lock_type(self) -> str:
        """Get lock type: 'min', 'center', or 'max'. Only valid if is_lock_mode."""
        lock_id = self.lock_picker.current_button_id
        return ["min", "center", "max"][lock_id]

    @property
    def lock_node_id(self) -> str | None:
        """Get the lock target node ID. Returns BOXY_ID for boxy, or meshbox node ID."""
        if self.lock_node_combo.currentIndex() >= 0:
            return self.lock_node_combo.currentData()
        return self.BOXY_ID

    @property
    def is_locked_to_boxy(self) -> bool:
        """True if locked to boxy (default behavior)."""
        return self.lock_node_id == self.BOXY_ID

    def set_available_nodes(self, nodes: list[tuple[str, str]], exclude_id: str | None = None):
        """Set the available nodes for locking to.

        Args:
            nodes: List of (node_id, node_name) tuples for meshbox nodes.
            exclude_id: Node ID to exclude (typically the current node).
        """
        self.lock_node_combo.blockSignals(True)
        current_id = self.lock_node_combo.currentData()
        self.lock_node_combo.clear()

        # Always add Boxy as first option
        self.lock_node_combo.addItem("Boxy", self.BOXY_ID)

        # Add meshbox nodes
        for node_id, node_name in nodes:
            if node_id != exclude_id:
                self.lock_node_combo.addItem(node_name, node_id)

        # Restore selection if still valid
        if current_id:
            idx = self.lock_node_combo.findData(current_id)
            if idx >= 0:
                self.lock_node_combo.setCurrentIndex(idx)
        self.lock_node_combo.blockSignals(False)

    def set_mode(self, mode: str, constant_value: float = 50.0, lock_node_id: str | None = None):
        """Set the size mode.

        Args:
            mode: 'constant', 'min', 'center', or 'max'
            constant_value: Value to use if mode is 'constant'
            lock_node_id: Node ID to lock to (None or BOXY_ID for boxy)
        """
        if mode == "constant":
            self.radio_button_widget.set_button_id(self.MODE_CONSTANT)
            self.spin_box.setValue(constant_value)
        else:
            # Lock modes: min, center, max
            self.radio_button_widget.set_button_id(self.MODE_LOCK)
            lock_id = {"min": 0, "center": 1, "max": 2}.get(mode, 2)
            self.lock_picker.set_button_id(lock_id)
            # Set lock target node
            if lock_node_id:
                idx = self.lock_node_combo.findData(lock_node_id)
                if idx >= 0:
                    self.lock_node_combo.setCurrentIndex(idx)
            else:
                self.lock_node_combo.setCurrentIndex(0)  # Default to Boxy
        self.update_ui()


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = SizeWidget()
    widget.show()
    app.exec()
