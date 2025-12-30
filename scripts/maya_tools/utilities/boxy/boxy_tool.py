"""UI for Boxy."""
import contextlib

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QComboBox, QColorDialog, QLabel, QLineEdit, QSizePolicy

from core import color_classes, DEVELOPER
from core.color_classes import RGBColor
from core.core_enums import Side
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from widgets.button_bar import ButtonBar
from widgets.clickable_label import ClickableLabel
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget

with contextlib.suppress(ImportError):
    from maya_tools.utilities.boxy import boxy

TOOL_NAME = "Boxy Tool"
VERSIONS = Versions(
    versions=[
        VersionInfo(name=TOOL_NAME, version="1.0", codename="cobra", info="first release"),
    ]
)

class BoxyTool(GenericWidget):
    """Boxy UI Class."""
    color_key = "color"
    default_name = "boxy"
    pivot_index = "pivot_index"

    def __init__(self):
        super().__init__(title=VERSIONS.title, margin=8, spacing=8)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        left_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        grid = self.add_group_box(GridWidget(title="Boxy Parameters", spacing=8))
        grid.add_label(text="Pivot Position", row=0, column=0, alignment=left_alignment)
        self.pivot_combo_box: QComboBox = grid.add_combo_box(items=["bottom", "center", "top"], default_index=1, row=0, column=1)
        grid.add_label(text="Wirefame Color", row=1, column=0, alignment=left_alignment)
        self.color_picker: ClickableLabel = grid.add_widget(widget=ClickableLabel(""), row=1, column=1)
        grid.add_label(text="Base Name", row=2, column=0, alignment=left_alignment)
        self.name_field = grid.add_widget(widget=QLineEdit(self.default_name), row=2, column=1)
        grid.add_label(text="Inherit Rotation", row=3, column=0, alignment=left_alignment)
        self.rotation_check_box = grid.add_widget(widget=QCheckBox(), row=3, column=1)
        self.create_button = self.add_button(
            text="Create", tool_tip="Create boxy object", clicked=self.create_button_clicked)
        self.info_label = self.add_label(text="Ready...", side=Side.left)
        default_color = self.settings.value(self.color_key, color_classes.DEEP_GREEN.values)
        self.wireframe_color = RGBColor(*default_color)
        self._setup_ui()

    def _setup_ui(self):
        """Set up ui."""
        self.color_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.name_field.setPlaceholderText("Enter base name...")
        self.rotation_check_box.setChecked(True)
        self.setFixedHeight(self.sizeHint().height())
        self.color_picker.clicked.connect(self.color_picker_clicked)
        self.pivot_combo_box.setCurrentIndex(self.settings.value(self.pivot_index, 1))
        self.pivot_combo_box.currentIndexChanged.connect(self.pivot_combo_box_index_changed)

    @property
    def info(self) -> str:
        """Text value of the info label."""
        return self.info_label.text()

    @info.setter
    def info(self, text: str) -> None:
        self.info_label.setText(text)

    @property
    def inherit_rotations(self) -> bool:
        """Value of the rotation check box."""
        return self.rotation_check_box.isChecked()

    @property
    def pivot(self) -> Side:
        return Side[self.pivot_combo_box.currentText()]

    @property
    def wireframe_color(self) -> RGBColor:
        """Color for the boxy wireframe."""
        return self._wireframe_color

    @wireframe_color.setter
    def wireframe_color(self, value: RGBColor):
        self._wireframe_color = value
        self.color_picker.setStyleSheet(f"background-color: {value.css};")
        self.settings.setValue(self.color_key, value.values)

    def color_picker_clicked(self):
        """Event for color-picker."""
        default = QColor()
        default.setRgb(*self.wireframe_color.values)
        color = QColorDialog.getColor(default)
        if color.isValid():
            self.wireframe_color = RGBColor(color.red(), color.green(), color.blue())

    def create_button_clicked(self):
        """Event for create button."""
        creator = boxy.Boxy(color=self.wireframe_color)
        creator.create(pivot=self.pivot, inherit_rotations=self.inherit_rotations)

    def pivot_combo_box_index_changed(self, arg):
        """Event for pivot combo box."""
        self.settings.setValue(self.pivot_index, arg)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    window = BoxyTool()
    window.show()
    app.exec()
