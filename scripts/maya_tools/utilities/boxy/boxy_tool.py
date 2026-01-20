"""UI for Boxy."""
import contextlib

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QComboBox, QColorDialog, QDoubleSpinBox, QLineEdit, QSizePolicy

from core import color_classes, DEVELOPER
from core.color_classes import RGBColor
from core.core_enums import Side
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from maya_tools import maya_widget_utils, node_utils
from maya_tools.utilities.boxy import UI_SCRIPT
from widgets.button_bar import ButtonBar
from widgets.clickable_label import ClickableLabel
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.image_label import ImageLabel

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools.utilities.boxy import boxy

TOOL_NAME = "Boxy Tool"
VERSIONS = Versions(
    versions=[
        VersionInfo(name=TOOL_NAME, version="1.0.0", codename="cobra", info="first release"),
        VersionInfo(name=TOOL_NAME, version="1.0.1", codename="banshee", info="size field added"),
        VersionInfo(name=TOOL_NAME, version="1.0.2", codename="newt", info="issue fixed for nodes with children"),
        VersionInfo(name=TOOL_NAME, version="1.0.3", codename="panther wip", info="button functions added"),
    ]
)

class BoxyTool(GenericWidget):
    """Boxy UI Class."""
    color_key = "color"
    default_name = "boxy"
    pivot_index = "pivot_index"
    size_key = "size"

    def __init__(self):
        super().__init__(title=VERSIONS.title, margin=8, spacing=8)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self.logo = self.add_widget(ImageLabel(image_path("boxy_logo.png")))
        left_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        button_bar: ButtonBar = self.add_widget(ButtonBar(button_size=32))
        button_bar.add_icon_button(icon_path=image_path("boxy.png"), tool_tip="Generate boxy", clicked=self.create_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_to_cube.png"), tool_tip="Toggle Boxy/Poly-Cube", clicked=self.boxy_cube_toggle_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_concave.png"), tool_tip="Concave boxy from face", clicked=self.concave_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_convex.png"), tool_tip="Convex boxy from face", clicked=self.convex_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("help.png"), tool_tip="Help", clicked=self.help_button_clicked)
        grid: GridWidget = self.add_group_box(GridWidget(title="Boxy Parameters", spacing=8))
        grid.add_label(text="Pivot Position", row=0, column=0, alignment=left_alignment)
        self.pivot_combo_box: QComboBox = grid.add_combo_box(items=["bottom", "center", "top"], default_index=1, row=0, column=1)
        grid.add_label(text="Wirefame Color", row=1, column=0, alignment=left_alignment)
        self.color_picker: ClickableLabel = grid.add_widget(widget=ClickableLabel(""), row=1, column=1)
        grid.add_label(text="Base Name", row=2, column=0, alignment=left_alignment)
        self.name_field = grid.add_widget(widget=QLineEdit(self.default_name), row=2, column=1)
        grid.add_label(text="Default Size", row=3, column=0, alignment=left_alignment)
        self.size_field: QDoubleSpinBox = grid.add_widget(widget=QDoubleSpinBox(), row=3, column=1)
        grid.add_label(text="Inherit Rotation", row=4, column=0, alignment=left_alignment)
        self.rotation_check_box = grid.add_widget(widget=QCheckBox(), row=4, column=1)
        self.info_label = self.add_label(text="Ready...", side=Side.left)
        default_color = self.settings.value(self.color_key, color_classes.DEEP_GREEN.values)
        self.wireframe_color = RGBColor(*default_color)
        self._setup_ui()

    def _setup_ui(self):
        """Set up ui."""
        self.color_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.name_field.setPlaceholderText("Enter base name...")
        self.rotation_check_box.setChecked(True)
        self.color_picker.clicked.connect(self.color_picker_clicked)
        self.pivot_combo_box.setCurrentIndex(self.settings.value(self.pivot_index, 1))
        self.pivot_combo_box.currentIndexChanged.connect(self.pivot_combo_box_index_changed)
        self.size_field.setValue(self.settings.value(self.size_key, 10.0))
        self.size_field.setRange(0.1, 100000.0)
        self.size_field.setDecimals(1)
        self.size_field.setSingleStep(0.1)
        self.size_field.valueChanged.connect(self.size_field_value_changed)
        self.logo.setFixedSize(self.sizeHint().width(), 80)
        self.setFixedSize(self.sizeHint())

    @property
    def default_size(self):
        """Default size."""
        return self.size_field.value()

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

    def concave_face_button_clicked(self):
        """Event for concave face button."""
        self.info = "Concave face button clicked."

    def convex_face_button_clicked(self):
        """Event for convex face button."""
        self.info = "Convex face button clicked."

    def create_button_clicked(self):
        """Event for create button."""
        selection = cmds.ls(selection=True)
        creator = boxy.Boxy(color=self.wireframe_color)
        boxy_items, exceptions = creator.create(
            pivot=self.pivot, inherit_rotations=self.inherit_rotations, default_size=self.default_size)
        if len(exceptions) > 0:
            exception_string = ", ".join(ex.message for ex in exceptions)
            self.info = f"Issues found: {exception_string}"
        elif len(boxy_items) == 0:
            self.info = "No boxy objects created."
            cmds.select(selection)
        else:
            if len(boxy_items) == 1:
                self.info = f"Boxy object created: {boxy_items[0]}"
            else:
                self.info = f"Boxy objects created: {', '.join(boxy_items)}"
            cmds.select(boxy_items)

    def help_button_clicked(self):
        """Event for help button."""
        self.info = "Help button clicked."

    def pivot_combo_box_index_changed(self, arg):
        """Event for pivot combo box."""
        self.settings.setValue(self.pivot_index, arg)

    def boxy_cube_toggle_clicked(self):
        """Event for boxy cube toggle button."""
        self.info = "Boxy cube toggle clicked."
        selection_list = []
        boxy_nodes = boxy.get_selected_boxy_nodes()
        poly_cubes = boxy.get_selected_poly_cubes()
        for boxy_node in boxy_nodes:
            selection_list.append(boxy.convert_boxy_to_poly_cube(node=boxy_node))
        for poly_cube in poly_cubes:
            selection_list.append(boxy.convert_poly_cube_to_boxy(node=poly_cube))
        if selection_list:
            cmds.select(selection_list)

    def size_field_value_changed(self, arg):
        """Event for size field."""
        self.settings.setValue(self.size_key, arg)


def launch():
    """Launch Boxy Tool."""
    maya_widget_utils.launch_tool(
        tool_module="maya_tools.utilities.boxy.boxy_tool",
        tool_class="BoxyTool",
        use_workspace_control=True,
        ui_script="from maya_tools.utilities.boxy import boxy_tool; boxy_tool.BoxyTool().restore()",
    )

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    window = BoxyTool()
    window.show()
    app.exec()
