# Staircase Creator Tool

import contextlib

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDoubleSpinBox

from core import color_classes, DEVELOPER
from core.core_enums import Axis, Side
from core.point_classes import Point3
from core.core_paths import image_path
from core.version_info import VersionInfo, Versions
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import helpers, node_utils
    from maya_tools.utilities.arch_tools import door_creator, LOCATOR_COLOR, staircase_creator

TOOL_NAME = "Arch Tools"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release")])


class ArchTools(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    locator_size = 10.0

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        buttons: ButtonBar = self.add_widget(ButtonBar())
        buttons.add_icon_button(
            icon_path=image_path("edit.png"), tool_tip="Edit Stairs", clicked=self.edit_button_clicked)
        general_form: FormWidget = self.add_group_box(FormWidget(title="General Attributes"))
        self.axis_combo_box = general_form.add_combo_box(label="Axis", items=("x", "z"), default_index=1)
        self.angle_input = general_form.add_float_field(label="Angle", default_value=0.0, minimum=-180.0, maximum=180.0)
        self.auto_texture_check_box = general_form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        self.staircase_form: FormWidget = self.add_group_box(FormWidget(title="Staircase Creator"))
        self.rise_input = self.staircase_form.add_float_field(
            label="Target rise", default_value=20.0, minimum=1.0, maximum=200.0, step=1.0)
        self.staircase_form.add_button(
            label="Create Staircase Locators",
            tool_tip="Create Staircase Locators",
            clicked=self.staircase_locators_button_clicked)
        self.staircase_form.add_button(
            label="Create Stairs", clicked=self.stairs_button_clicked, tool_tip="Create Stairs")
        self.door_form: FormWidget = self.add_group_box(FormWidget(title="Door Creator"))
        self.door_trim_thickness: QDoubleSpinBox = self.door_form.add_float_field(
            label="Trim Thickness", default_value=2.0, minimum=0.5, maximum=5.0, step=0.1)
        self.door_skirt_input: QDoubleSpinBox = self.door_form.add_float_field(
            label="Skirt Thickness", default_value=10.0, minimum=0.5, maximum=30.0, step=1.0)
        self.door_thickness_input: QDoubleSpinBox = self.door_form.add_float_field(
            label="Door Thickness", default_value=5.0, minimum=1.0, maximum=20.0, step=0.1)
        self.door_form.add_check_box(label="Left/Right")
        self.door_form.add_button(
            label="Create Door Locators", tool_tip="Create Door Locators", clicked=self.door_locators_button_clicked)
        self.door_form.add_button(
            label="Create Door", clicked=self.door_button_clicked, tool_tip="Create Doors")
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

    @property
    def door_thickness(self) -> float:
        return self.door_thickness_input.value()

    @property
    def door_skirt(self) -> float:
        return self.door_skirt_input.value()

    @property
    def door_trim(self) -> float:
        return self.door_trim_thickness.value()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    def auto_texture_check_box_state_changed(self):
        """Event for auto_texture_check_box."""
        self.settings.setValue(self.auto_texture_check_box_state, self.auto_texture)

    def staircase_locators_button_clicked(self):
        """Event for staircase locators button."""
        locators = []
        for i in range(2):
            position = Point3(i * 100, i * 250, i * -300)
            locators.append(helpers.create_locator(position=position, name=f"staircase_locator{i}", size=self.locator_size, color=LOCATOR_COLOR))
        cmds.select(locators)

    def door_locators_button_clicked(self):
        """Event for door locators button."""
        locators = []
        for i in range(2):
            position = Point3(i * 80, i * 200, i * -10)
            locators.append(helpers.create_locator(position=position, name=f"door_locator{i}", size=self.locator_size, color=LOCATOR_COLOR))
        cmds.select(locators)

    def door_button_clicked(self):
        """Event for door button."""
        self.info = "Door button clicked"
        new_objects = []
        # now deal with any locators
        locators = helpers.get_selected_locators()
        if len(locators) == 0:
            self.door_locators_button_clicked()
        elif len(locators) == 2:
            cmds.select(locators)
        else:
            self.info = "Please select two locators."
            return
        try:
            creator = door_creator.DoorCreator(trim=self.door_trim, skirt=self.door_skirt, door_thickness=self.door_thickness)
            door = creator.create(auto_texture=self.auto_texture)
            # self.info = f"Door created: {door}"
            # new_objects.append(door)
        except AssertionError as e:
            self.info = str(e)
        if new_objects:
            cmds.select(new_objects)

    def edit_button_clicked(self):
        """Event for edit button."""
        for x in node_utils.get_selected_transforms():
            locators, target_rise, axis = staircase_creator.restore_locators_from_staircase(node=x)
            self.rise_input.setValue(target_rise)
            self.axis_combo_box.setCurrentText(axis.name)
            cmds.select(locators)

    def stairs_button_clicked(self):
        """Event for stairs button."""
        new_objects = []
        selected_transforms = node_utils.get_selected_transforms()

        # any selected staircases, we handle first
        staircases = [x for x in selected_transforms if node_utils.is_staircase(x)]
        for staircase in staircases:
            locators, _, _ = staircase_creator.restore_locators_from_staircase(node=staircase)
            cmds.select(locators)
            creator = staircase_creator.StaircaseCreator(default_rise=self.rise_input.value(), axis=self.axis)
            new_objects.append(creator.create(auto_texture=self.auto_texture))

        # now deal with any locators
        locators = [x for x in selected_transforms if node_utils.is_locator(x)]
        if len(locators) == 0:
            self.staircase_locators_button_clicked()
        elif len(locators) == 2:
            cmds.select(locators)
        else:
            self.info = "Please select two locators."
            return
        try:
            creator = staircase_creator.StaircaseCreator(default_rise=self.rise_input.value(), axis=self.axis)
            staircase = creator.create(auto_texture=self.auto_texture)
            self.info = f"Stairs created: {staircase}"
            new_objects.append(staircase)
        except AssertionError as e:
            self.info = str(e)
        if new_objects:
            cmds.select(new_objects)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = ArchTools()
    tool.show()
    app.exec_()
