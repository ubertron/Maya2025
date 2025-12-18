# Staircase Creator Tool

from maya import cmds
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

from maya_tools import helpers, node_utils
from maya_tools.utilities.architools import door_creator, LOCATOR_COLOR, staircase_creator

TOOL_NAME = "Architools"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="0.0.1", codename="hawk", info="first_release"),
    VersionInfo(name=TOOL_NAME, version="0.0.2", codename="funky chicken", info="generics added"),
])


class Architools(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    locator_size = 10.0

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        buttons: ButtonBar = self.add_widget(ButtonBar())
        buttons.add_icon_button(
            icon_path=image_path("edit.png"), tool_tip="Edit Stairs", clicked=self.edit_button_clicked)
        general_form: FormWidget = self.add_group_box(FormWidget(title="General Attributes"))
        self.skirt_thickness_input: QDoubleSpinBox = general_form.add_float_field(
            label="Skirt Thickness", default_value=2.0, minimum=0.5, maximum=5.0, step=0.1)
        self.auto_texture_check_box = general_form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        self.staircase_form: FormWidget = self.add_group_box(FormWidget(title="Staircase Creator"))
        self.rise_input = self.staircase_form.add_float_field(
            label="Target rise", default_value=20.0, minimum=1.0, maximum=200.0, step=1.0)
        self.axis_combo_box = self.staircase_form.add_combo_box(label="Axis", items=("x", "z"), default_index=1)
        self.staircase_form.add_button(
            label="Create Staircase Locators",
            tool_tip="Create Staircase Locators",
            clicked=self.staircase_locators_button_clicked)
        self.staircase_form.add_button(
            label="Create Stairs", clicked=self.stairs_button_clicked, tool_tip="Create Stairs")
        self.door_form: FormWidget = self.add_group_box(FormWidget(title="Door Creator"))
        self.door_frame_input: QDoubleSpinBox = self.door_form.add_float_field(
            label="Frame Size", default_value=10.0, minimum=0.5, maximum=30.0, step=1.0)
        self.door_depth_input: QDoubleSpinBox = self.door_form.add_float_field(
            label="Door Depth", default_value=5.0, minimum=1.0, maximum=20.0, step=0.1)
        self.door_form.add_combo_box(label="Hinge Side", items=("Left", "Right"), default_index=0)
        self.door_form.add_combo_box(label="Opening Side", items=("Front", "Back"), default_index=0)
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
    def door_depth(self) -> float:
        return self.door_depth_input.value()

    @property
    def frame_size(self) -> float:
        return self.door_frame_input.value()

    @property
    def skirt_thickness(self) -> float:
        return self.skirt_thickness_input.value()

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
        try:
            creator = door_creator.DoorCreator(skirt=self.skirt_thickness, frame=self.frame_size,
                                               door_depth=self.door_depth)
            door = creator.create(auto_texture=self.auto_texture)
            self.info = f"Door created: {door}"
            new_objects.append(door)
        except AssertionError as e:
            self.info = str(e)

        if new_objects:
            cmds.select(new_objects)

    def door_button_clicked_(self):
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
            creator = door_creator.DoorCreator(skirt=self.skirt_thickness, frame=self.frame_size, door_depth=self.door_depth)
            door = creator.create(auto_texture=self.auto_texture)
            self.info = f"Door created: {door}"
            new_objects.append(door)
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
    tool = Architools()
    tool.show()
    app.exec_()
