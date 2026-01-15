# Staircase Creator Tool
from __future__ import annotations

import contextlib
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDoubleSpinBox, QTabWidget

from core import DEVELOPER
from core.core_enums import Axis, Side
from core.point_classes import Point3Pair, X_AXIS, Z_AXIS
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from maya_tools.utilities.architools import TOOL_NAME
from maya_tools.utilities.architools.widgets.door_widget import DoorWidget
from maya_tools.utilities.architools.widgets.staircase_widget import StaircaseWidget
from maya_tools.utilities.architools.widgets.window_widget import WindowWidget
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils
    from maya_tools.utilities.boxy import boxy

VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release"),
    VersionInfo(name=TOOL_NAME, version="0.0.2", codename="funky chicken", info="generics added"),
    VersionInfo(name=TOOL_NAME, version="0.0.3", codename="funky pigeon", info="tabs added"),
    VersionInfo(name=TOOL_NAME, version="0.0.4", codename="leopard", info="boxy integration"),
    VersionInfo(name=TOOL_NAME, version="0.0.5", codename="banshee", info="boxy-based staircase"),
    VersionInfo(name=TOOL_NAME, version="0.0.6", codename="squirrel", info="window added"),
])


class Architools(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    default_size = 100.0
    skirt_thickness_key = "skirt_thickness"
    tab_index_key = "tab_index"

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        buttons: ButtonBar = self.add_widget(ButtonBar())
        buttons.add_icon_button(
            icon_path=image_path("boxy.png"), tool_tip="Create Base-Pivot Boxy", clicked=self.boxy_clicked)
        buttons.add_stretch()
        general_form: FormWidget = self.add_group_box(FormWidget(title="General Attributes"))
        self.skirt_thickness_input: QDoubleSpinBox = general_form.add_float_field(
            label="Skirt Thickness", default_value=2.0, minimum=0.5, maximum=5.0, step=0.1)
        self.auto_texture_check_box = general_form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        self.tab_widget: QTabWidget = self.add_widget(QTabWidget())
        self.tab_widget.addTab(DoorWidget(parent=self), DoorWidget().windowTitle())
        self.tab_widget.addTab(StaircaseWidget(parent=self), StaircaseWidget().windowTitle())
        self.tab_widget.addTab(WindowWidget(parent=self), WindowWidget().windowTitle())
        self.info_label = self.add_label("Ready...", side=Side.left)
        self._setup_ui()

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
        for x in boxy.Boxy().create(
                pivot=Side.bottom, inherit_rotations=True, default_size=self.default_size):
            bounds: Point3Pair = node_utils.get_min_max_points(node=x, inherit_rotations=True)
            dot_x = abs(Point3Pair(bounds.min_max_vector, X_AXIS).dot_product)
            dot_z = abs(Point3Pair(bounds.min_max_vector, Z_AXIS).dot_product)
            if dot_z > dot_x:
                boxy.edit_boxy_orientation(node=x, rotation=-90, axis=Axis.y)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    tool = Architools()
    tool.show()
    app.exec_()
