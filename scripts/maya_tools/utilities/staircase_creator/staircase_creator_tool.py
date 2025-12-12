# Staircase Creator Tool

import contextlib

from PySide6.QtCore import QSettings

from core import DEVELOPER
from core.core_enums import Axis, Side
from core.point_classes import Point3
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import locator_utils, node_utils
    from maya_tools.utilities.staircase_creator import staircase_creator

TOOL_NAME = "Staircase Creator"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release")])


class StaircaseCreatorTool(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        buttons: ButtonBar = self.add_widget(ButtonBar())
        buttons.add_icon_button(
            icon_path=image_path("locators.png"), tool_tip="Create Locators", clicked=self.locators_button_clicked)
        buttons.add_icon_button(
            icon_path=image_path("stairs.png"), tool_tip="Create Stairs", clicked=self.stairs_button_clicked)
        buttons.add_icon_button(
            icon_path=image_path("edit.png"), tool_tip="Edit Stairs", clicked=self.edit_button_clicked)
        form: FormWidget = self.add_widget(FormWidget())
        self.rise_input = form.add_float_field(
            label="Target rise", default_value=20.0, minimum=1.0, maximum=200.0, step=1.0)
        self.axis_combo_box = form.add_combo_box(label="Axis", items=("x", "z"), default_index=1)
        self.auto_texture_check_box = form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        buttons.add_stretch()
        self.add_stretch()
        self.info_label = self.add_label("Ready...", side=Side.left)
        self._setup_ui()

    def _setup_ui(self):
        auto_texture_check_box_state = self.settings.value(self.auto_texture_check_box_state, True)
        self.auto_texture_check_box.setChecked(auto_texture_check_box_state)
        self.auto_texture_check_box.stateChanged.connect(self.auto_texture_check_box_state_changed)

    @property
    def axis(self) -> Axis:
        return Axis[self.axis_combo_box.currentText()]

    @property
    def info(self) -> str:
        return self.info_label.text()

    @property
    def auto_texture(self) -> bool:
        return self.auto_texture_check_box.isChecked()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    def auto_texture_check_box_state_changed(self):
        """Event for auto_texture_check_box."""
        self.settings.setValue(self.auto_texture_check_box_state, self.auto_texture)

    @staticmethod
    def locators_button_clicked(self):
        """Event for locators button."""
        locators = []
        for i in range(2):
            position = Point3(i * 100, i * 250, i * -300)
            locators.append(locator_utils.create_locator(position=position, name=f"staircase_locator{i}", size=25.0))
        cmds.select(locators)

    def edit_button_clicked(self):
        """Event for edit button."""
        for x in node_utils.get_selected_transforms():
            locators, target_rise, axis = staircase_creator.restore_locators_from_staircase(node=x)
            self.rise_input.setValue(target_rise)
            self.axis_combo_box.setCurrentText(axis.name)
            cmds.select(locators)

    def stairs_button_clicked(self):
        try:
            creator = staircase_creator.StaircaseCreator(default_rise=self.rise_input.value(), axis=self.axis)
            creator.create(auto_texture=True)
            self.info = "Stairs created"
        except AssertionError as e:
            self.info = str(e)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = StaircaseCreatorTool()
    tool.show()
    app.exec_()
