"""
ROBOTOOLS PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
# UI for Boxy.
import contextlib

from qtpy.QtCore import Qt, QSettings
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QCheckBox, QComboBox, QColorDialog, QDoubleSpinBox, QSizePolicy

from core import color_classes, DEVELOPER
from core.color_classes import RGBColor
from core.core_enums import ComponentType, Side, SurfaceDirection
from core.core_paths import image_path
from maya_tools.utilities.boxy import boxy_utils, VERSIONS, TOOL_NAME
from widgets.button_bar import ButtonBar
from widgets.clickable_label import ClickableLabel
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.image_label import ImageLabel

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import maya_widget_utils, node_utils
    from maya_tools.geometry import face_finder
    from maya_tools.geometry.component_utils import FaceComponent, components_from_selection
    from maya_tools.utilities.boxy import BoxyException


class BoxyTool(GenericWidget):
    """Boxy UI Class."""
    color_key = "color"
    inherit_rotation_key = "inherit_rotation"
    inherit_scale_key = "inherit_scale"
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
        self.pivot_combo_box: QComboBox = grid.add_combo_box(items=["bottom", "center", "top", "left", "right", "front", "back"], default_index=1, row=0, column=1)
        grid.add_label(text="Wireframe Color", row=1, column=0, alignment=left_alignment)
        self.color_picker: ClickableLabel = grid.add_widget(widget=ClickableLabel(""), row=1, column=1)
        grid.add_label(text="Default Size", row=2, column=0, alignment=left_alignment)
        self.size_field: QDoubleSpinBox = grid.add_widget(widget=QDoubleSpinBox(), row=2, column=1)
        grid.add_label(text="Inherit Rotation", row=3, column=0, alignment=left_alignment)
        self.rotation_check_box: QCheckBox = grid.add_widget(widget=QCheckBox(), row=3, column=1)
        grid.add_label(text="Inherit Scale", row=4, column=0, alignment=left_alignment)
        self.scale_check_box: QCheckBox = grid.add_widget(widget=QCheckBox(), row=4, column=1)
        self.info_label = self.add_label(text="Ready...", side=Side.left)
        default_color = self.settings.value(self.color_key, color_classes.DEEP_GREEN.values)
        self.wireframe_color = RGBColor(*default_color)
        self._setup_ui()

    def _create_boxy_from_face(self, surface_direction: SurfaceDirection):
        """Create a Boxy from a selected face and its opposite face."""
        components = components_from_selection()

        # Validate single face selection
        if len(components) != 1 or not isinstance(components[0], FaceComponent):
            self.info = "Select a single face"
            return

        face = components[0]

        # Find opposite face
        opposite = face_finder.get_opposite_face(
            component=face,
            surface_direction=surface_direction,
            select=False
        )

        if opposite is None:
            self.info = "No matching face found"
            return

        # Select both faces and create Boxy
        cmds.select([face.name, opposite.name], replace=True)
        cmds.hilite(face.transform)
        self.create_button_clicked()

    def _setup_ui(self):
        """Set up ui."""
        self.color_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.rotation_check_box.setChecked(self.settings.value(self.inherit_rotation_key, True))
        self.rotation_check_box.stateChanged.connect(self.rotation_check_box_state_changed)
        self.scale_check_box.setChecked(self.settings.value(self.inherit_scale_key, True))
        self.scale_check_box.stateChanged.connect(self.scale_check_box_state_changed)
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
    def inherit_rotation(self) -> bool:
        """Value of the rotation check box."""
        return self.rotation_check_box.isChecked()

    @property
    def inherit_scale(self) -> bool:
        """Value of the rotation check box."""
        return self.scale_check_box.isChecked()

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
        self._create_boxy_from_face(surface_direction=SurfaceDirection.concave)

    def convex_face_button_clicked(self):
        """Event for convex face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.convex)

    def create_button_clicked(self):
        """Event for create button."""
        selection = cmds.ls(selection=True)
        creator = boxy_utils.Boxy(color=self.wireframe_color)
        boxy_nodes, exceptions = creator.create(
            pivot=self.pivot, inherit_rotations=self.inherit_rotation,
            inherit_scale=self.inherit_scale, default_size=self.default_size)
        if len(exceptions) > 0:
            exception_string = ", ".join(ex.message for ex in exceptions)
            self.info = f"Issues found: {exception_string}"
        elif len(boxy_nodes) == 0:
            self.info = "No boxy objects created."
            cmds.select(selection)
        else:
            if len(boxy_nodes) == 1:
                self.info = f"Boxy object created: {boxy_nodes[0]}"
            else:
                self.info = f"Boxy objects created: {', '.join(boxy_nodes)}"
            cmds.select(boxy_nodes)
            node_utils.set_component_mode(ComponentType.object)

    def help_button_clicked(self):
        """Event for help button."""
        from maya_tools.utilities.boxy.boxy_help import BoxyHelp
        help_widgets = maya_widget_utils.get_widget_instances(tool_class="BoxyHelp")
        help_widget = help_widgets[-1] if help_widgets else BoxyHelp(parent_widget=self)
        # help_widget.setWindowModality(Qt.WindowModality.ApplicationModal)
        help_widget.show()

    def pivot_combo_box_index_changed(self, arg):
        """Event for pivot combo box."""
        self.settings.setValue(self.pivot_index, arg)

    def boxy_cube_toggle_clicked(self):
        """Event for boxy cube toggle button."""
        selection_list = []
        exceptions = []
        boxy_nodes = boxy_utils.get_selected_boxy_nodes()
        poly_cubes = boxy_utils.get_selected_poly_cubes()
        for boxy_node in boxy_nodes:
            result = boxy_utils.convert_boxy_to_poly_cube(node=boxy_node)
            if isinstance(result, BoxyException):
                exceptions.append(result)
            else:
                selection_list.append(result)
        for poly_cube in poly_cubes:
            result = boxy_utils.convert_poly_cube_to_boxy(node=poly_cube, color=self.wireframe_color)
            if isinstance(result, BoxyException):
                exceptions.append(result)
            else:
                selection_list.append(result)
        if exceptions:
            exception_string = ", ".join(ex.message for ex in exceptions)
            self.info = f"Issues found: {exception_string}"
        elif selection_list:
            self.info = f"Toggled: {', '.join(selection_list)}"
            cmds.select(selection_list)
        else:
            self.info = "No valid selection for toggle."

    def rotation_check_box_state_changed(self):
        """Event for scale checkbox state change."""
        self.settings.setValue(self.inherit_rotation_key, self.inherit_rotation)

    def scale_check_box_state_changed(self):
        """Event for scale checkbox state change."""
        self.settings.setValue(self.inherit_scale_key, self.inherit_scale)

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
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    window = BoxyTool()
    window.show()
    app.exec()
