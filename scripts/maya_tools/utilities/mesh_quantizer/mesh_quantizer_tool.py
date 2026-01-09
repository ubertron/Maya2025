"""Mesh Quantizer Tool"""
import contextlib
import sys

from PySide6.QtWidgets import QDoubleSpinBox, QSizePolicy
from PySide6.QtCore import QSettings

from core import DEVELOPER
from core.version_info import VersionInfo
from core.core_paths import image_path
from widgets.button_bar import ButtonBar
from widgets.generic_widget import GenericWidget
from widgets.vector_input_widget import VectorInputWidget

with contextlib.suppress(ImportError):
    from maya_tools import display_utils, geometry_utils, node_utils
    from maya_tools.utilities.mesh_quantizer import mesh_quantizer

TOOL_NAME = "Mesh Quantizer"
VERSIONS = (
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="predator", info="Initial version"),
    VersionInfo(name=TOOL_NAME, version="0.0.2", codename="terminator", info="Amount saved to settings"),
)

class MeshQuantizerTool(GenericWidget):
    minimum_quantize_amount = 0.001
    amount_key = "amount"

    def __init__(self):
        super().__init__(title=VERSIONS[-1].title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        button_bar.add_icon_button(
            icon_path=image_path("quantize.png"), tool_tip="Quantize", clicked=self.quantize_button_clicked)
        button_bar.add_icon_button(
            icon_path=image_path("jiggle.png"), tool_tip="Jiggle", clicked=self.jiggle_button_clicked)
        button_bar.add_icon_button(
            icon_path=image_path("format.png"), tool_tip="Format Vertices", clicked=self.format_button_clicked)
        button_bar.add_stretch()
        self.add_stretch()
        self.default = self.settings.value(self.amount_key, 1.0)
        row = self.add_widget(ButtonBar())
        label = row.add_label("Amount:")
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.input_widget: QDoubleSpinBox = row.add_widget(widget=QDoubleSpinBox())
        self.info_label = self.add_label("Ready...")
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(300, self.sizeHint().height())
        self.input_widget.setValue(self.default)
        self.input_widget.setMinimum(0.0)
        self.input_widget.setMaximum(1000.0)
        self.input_widget.setSingleStep(0.1)
        self.input_widget.valueChanged.connect(lambda: self.settings.setValue(self.amount_key, self.amount))

    @property
    def amount(self) -> float:
        """Quantize amount."""
        return self.input_widget.value()

    @property
    def increment(self) -> float:
        return self.input_widget.value()

    @property
    def info(self) -> str:
        return self.info_label.text()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @staticmethod
    def format_button_clicked():
        """Event for format button."""
        print("format_button_clicked")
        selected_geometry = node_utils.get_selected_geometry()
        if len(selected_geometry) > 0:
            for x in selected_geometry:
                vertices = geometry_utils.get_vertex_positions(node=x)
                print(f"Object: {x}")
                print("\n".join(f"{idx} {str(v)}" for idx, v in enumerate(vertices)))
        else:
            display_utils.info_message("No geometry selected")

    def jiggle_button_clicked(self):
        """Event for jiggle button."""
        selected_geometry = node_utils.get_selected_geometry()
        if len(selected_geometry) > 0:
            for x in selected_geometry:
                mesh_quantizer.jiggle_vertices(node=x, distance=self.increment)
        else:
            display_utils.info_message("No geometry selected")

    def quantize_button_clicked(self):
        """Event for quantize button.

        Don't want to quantize custom_type nodes (i.e. procedural)
        """
        selected_geometry = [x for x in node_utils.get_selected_geometry() if not node_utils.is_custom_type_node(x)]
        count = 0
        if len(selected_geometry) > 0:
            for x in selected_geometry:
                vert_map = geometry_utils.get_vertex_positions(node=x)
                mesh_quantizer.quantize_vertices(node=x, increment=max(self.increment, self.minimum_quantize_amount))
                new_vert_map = geometry_utils.get_vertex_positions(node=x)
                changed = [idx for idx, v in enumerate(vert_map) if v != new_vert_map[idx]]
                count += len(changed)
            self.info = f"{count} vertices quantized"
        else:
            display_utils.info_message("No valid geometry selected")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QDoubleSpinBox

    app = QApplication(sys.argv)
    widget = MeshQuantizerTool()
    widget.show()
    app.exec()
