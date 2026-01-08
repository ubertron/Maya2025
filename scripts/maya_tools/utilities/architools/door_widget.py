from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox
from maya import cmds

from core.core_enums import Axis
from maya_tools import node_utils
from maya_tools.utilities.architools import door_creator
from maya_tools.utilities.architools.architools import ArchWidget
from maya_tools.utilities.boxy import boxy


class DoorWidget(ArchWidget):
    frame_size_key = "door_frame_size"
    depth_key = "door_depth"
    hinge_side_key = "door_hinge_side"
    opening_side_key = "door_opening_side"

    def __init__(self, parent=None):
        super().__init__(title="Door", parent=parent)
        default_frame_size = self.settings.value(self.frame_size_key, 10.0)
        default_depth = self.settings.value(self.depth_key, 5.0)
        default_hinge_side = self.settings.value(self.hinge_side_key, 0)
        default_opening_side = self.settings.value(self.opening_side_key, 0)
        self.door_frame_input: QDoubleSpinBox = self.form.add_float_field(
            label="Frame Size", default_value=default_frame_size, minimum=0.5, maximum=30.0, step=1.0)
        self.door_depth_input: QDoubleSpinBox = self.form.add_float_field(
            label="Door Depth", default_value=default_depth, minimum=1.0, maximum=20.0, step=0.1)
        self.hinge_combo_box = self.form.add_combo_box(
            label="Hinge Side", items=("Left", "Right"), default_index=default_hinge_side)
        self.opening_combo_box = self.form.add_combo_box(
            label="Opening Side", items=("Front", "Back"), default_index=default_opening_side)
        self._setup_ui()

    def _setup_ui(self):
        """Set up events."""
        self.door_frame_input.valueChanged.connect(lambda: self.settings.setValue(self.frame_size_key, self.door_frame_input.value()))
        self.door_depth_input.valueChanged.connect(lambda: self.settings.setValue(self.depth_key, self.door_depth_input.value()))
        self.hinge_combo_box.currentIndexChanged.connect(lambda: self.settings.setValue(self.hinge_side_key, self.hinge_combo_box.currentIndex()))
        self.opening_combo_box.currentIndexChanged.connect(lambda: self.settings.setValue(self.opening_side_key, self.opening_combo_box.currentIndex()))

    @property
    def door_depth(self) -> float:
        return self.door_depth_input.value()

    @property
    def frame_size(self) -> float:
        return self.door_frame_input.value()

    @property
    def skirt_thickness(self) -> float:
        return self.parent_widget.skirt_thickness_input.value()

    def convert_to_boxy_clicked(self):
        """Event for convert boxy button."""
        self.info = "Convert To Boxy clicked"
        for door in door_creator.get_selected_doors():
            door_creator.convert_door_to_boxy(door=door, delete=True)

    def convert_boxy_to_door(self) -> str | False:
        try:
            creator = door_creator.DoorCreator(
                skirt=self.skirt_thickness,
                frame=self.frame_size,
                door_depth=self.door_depth)
            return creator.create(auto_texture=self.parent_widget.auto_texture)
        except ValueError as e:
            LOGGER.debug(e)
            return False

    def create_button_clicked(self):
        """Event for door button."""
        self.info = "Door button clicked"
        new_objects = []
        try:
            for door in door_creator.get_selected_doors():
                door_creator.convert_door_to_boxy(door=door, delete=True)
            creator = door_creator.DoorCreator(
                skirt=self.skirt_thickness,
                frame=self.frame_size,
                door_depth=self.door_depth,
                auto_texture=self.parent_widget.auto_texture
            )
            door = creator.create()
            self.info = f"Door created: {door}"
            new_objects.append(door)
        except AssertionError as e:
            self.info = str(e)

        if new_objects:
            cmds.select(new_objects)

    def rotate_button_clicked(self):
        """Event for rotate button."""
        self.info = "Rotate button clicked"
        for x in node_utils.get_selected_transforms(full_path=True):
            if node_utils.is_door(x):
                temp_boxy = door_creator.convert_door_to_boxy(door=x, delete=True)
                boxy.edit_boxy_orientation(node=temp_boxy, rotation=-90, axis=Axis.y)
                self.convert_boxy_to_door()
            elif node_utils.is_boxy(x):
                boxy.edit_boxy_orientation(node=x, rotation=-90, axis=Axis.y)
