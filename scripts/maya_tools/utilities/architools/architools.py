# Staircase Creator Tool
from __future__ import annotations

import contextlib
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDoubleSpinBox, QTabWidget

from core import DEVELOPER
from core.core_enums import ComponentType, Side, SurfaceDirection
from core.core_paths import image_path
from maya_tools import maya_widget_utils
from maya_tools.utilities.architools import TOOL_NAME, VERSIONS, ARCHITOOLS_COLOR
from maya_tools.utilities.architools.widgets.door_widget import DoorWidget
from maya_tools.utilities.architools.widgets.staircase_widget import StaircaseWidget
from maya_tools.utilities.architools.widgets.window_widget import WindowWidget
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils
    from maya_tools.geometry import face_finder
    from maya_tools.geometry.component_utils import FaceComponent, components_from_selection
    from maya_tools.utilities.boxy import boxy_utils


class Architools(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    default_size = 100.0
    skirt_thickness_key = "skirt_thickness"
    tab_index_key = "tab_index"

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        button_bar.add_icon_button(
            icon_path=image_path("boxy.png"), tool_tip="Create Base-Pivot Boxy", clicked=self.boxy_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_to_cube.png"), tool_tip="Toggle Boxy/Poly-Cube", clicked=self.boxy_cube_toggle_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_concave.png"), tool_tip="Concave boxy from face",
                                   clicked=self.concave_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_convex.png"), tool_tip="Convex boxy from face",
                                   clicked=self.convex_face_button_clicked)
        button_bar.add_stretch()
        button_bar.add_icon_button(icon_path=image_path("help.png"), tool_tip="Help", clicked=self.help_button_clicked)
        general_form: FormWidget = self.add_group_box(FormWidget(title="General Attributes"))
        self.skirt_thickness_input: QDoubleSpinBox = general_form.add_float_field(
            label="Skirt Thickness", default_value=2.0, minimum=0.5, maximum=5.0, step=0.1)
        self.auto_texture_check_box = general_form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        self.tab_widget: QTabWidget = self.add_widget(QTabWidget())
        self.tab_widget.addTab(DoorWidget(parent=self), DoorWidget().windowTitle())
        self.tab_widget.addTab(WindowWidget(parent=self), WindowWidget().windowTitle())
        self.tab_widget.addTab(StaircaseWidget(parent=self), StaircaseWidget().windowTitle())
        self.info_label = self.add_label("Ready...", side=Side.left)
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
        self.boxy_clicked()

    def _setup_ui(self):
        auto_texture_check_box_state = self.settings.value(self.auto_texture_check_box_state, True)
        self.auto_texture_check_box.setChecked(auto_texture_check_box_state)
        self.auto_texture_check_box.stateChanged.connect(self.auto_texture_check_box_state_changed)
        self.skirt_thickness_input.setValue(self.settings.value(self.skirt_thickness_key, 2.0))
        self.skirt_thickness_input.valueChanged.connect(
            lambda: self.settings.setValue(self.skirt_thickness_key, self.skirt_thickness))
        self.tab_widget.setCurrentIndex(self.settings.value(self.tab_index_key, 0))
        self.tab_widget.currentChanged.connect(lambda: self.settings.setValue(
            self.tab_index_key, self.tab_widget.currentIndex()))

    @property
    def info(self) -> str:
        return self.info_label.text()

    @property
    def auto_texture(self) -> bool:
        return self.auto_texture_check_box.isChecked()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @property
    def skirt_thickness(self) -> float:
        return self.skirt_thickness_input.value()

    def auto_texture_check_box_state_changed(self):
        """Event for auto_texture_check_box."""
        self.settings.setValue(self.auto_texture_check_box_state, self.auto_texture)

    def boxy_clicked(self):
        """Event for main boxy button.

        Compare the min-max vector of the bounds to the X/Z axes to determine orientation
        """
        selection = cmds.ls(selection=True)
        creator: boxy_utils.Boxy = boxy_utils.Boxy(color=ARCHITOOLS_COLOR)
        boxy_items, exceptions = creator.create(
            pivot=Side.bottom, default_size=self.default_size)
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
            node_utils.set_component_mode(ComponentType.object)

    def boxy_cube_toggle_clicked(self):
        """Event for boxy cube toggle button."""
        selection_list, exceptions = boxy_utils.boxy_cube_toggle(wireframe_color=ARCHITOOLS_COLOR)
        if exceptions:
            exception_string = ", ".join(ex.message for ex in exceptions)
            self.info = f"Issues found: {exception_string}"
        elif selection_list:
            self.info = f"Toggled: {', '.join(selection_list)}"
            cmds.select(selection_list)
        else:
            self.info = "No valid selection for toggle."

    def concave_face_button_clicked(self):
        """Event for concave face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.concave)

    def convex_face_button_clicked(self):
        """Event for convex face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.convex)

    def help_button_clicked(self):
        """Event for help button."""
        # from maya_tools.utilities.architools.architools_help import ArchitoolsHelp
        # help_widgets = maya_widget_utils.get_widget_instances(tool_class="ArchitoolsHelp")
        # help_widget = help_widgets[-1] if help_widgets else ArchitoolsHelp(parent_widget=self)
        # help_widget.show()
        self.info = "Help button clicked"


def launch():
    """Launch Boxy Tool."""
    maya_widget_utils.launch_tool(
        tool_module="maya_tools.utilities.architools.architools",
        tool_class="Architools",
        use_workspace_control=True,
        ui_script="from maya_tools.utilities.architools import architools; architools.Architools().restore()",
    )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = Architools()
    tool.show()
    app.exec_()
