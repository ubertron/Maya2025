from __future__ import annotations

import logging

from maya import cmds
from PySide6.QtWidgets import QDoubleSpinBox

from core.core_enums import CustomType, Side
from core.logging_utils import get_logger
from maya_tools.utilities.architools import door_creator
from maya_tools.utilities.architools.widgets.arch_widget import ArchWidget

LOGGER = get_logger(__name__, level=logging.DEBUG)


class DoorWidget(ArchWidget):
    frame_size_key = "door_frame_size"
    depth_key = "door_depth"
    hinge_side_key = "door_hinge_side"
    opening_side_key = "door_opening_side"

    def __init__(self, parent=None):
        super().__init__(custom_type=CustomType.door, parent=parent)
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
        self.door_frame_input.valueChanged.connect(lambda: self.settings.setValue(self.frame_size_key, self.frame_size))
        self.door_depth_input.valueChanged.connect(lambda: self.settings.setValue(self.depth_key, self.door_depth))
        self.hinge_combo_box.currentIndexChanged.connect(lambda: self.settings.setValue(self.hinge_side_key, self.hinge_combo_box.currentIndex()))
        self.opening_combo_box.currentIndexChanged.connect(lambda: self.settings.setValue(self.opening_side_key, self.opening_combo_box.currentIndex()))

    @property
    def door_depth(self) -> float:
        return self.door_depth_input.value()

    @property
    def frame_size(self) -> float:
        return self.door_frame_input.value()

    @property
    def hinge_side(self) -> Side:
        return (Side.left, Side.right)[self.hinge_combo_box.currentIndex()]

    @property
    def opening_side(self) -> Side:
        return (Side.front, Side.back)[self.opening_combo_box.currentIndex()]

    @property
    def skirt_thickness(self) -> float:
        return self.parent_widget.skirt_thickness_input.value()

    def convert_boxy(self) -> str | False:
        try:
            creator = door_creator.DoorCreator(
                skirt=self.skirt_thickness,
                frame=self.frame_size,
                door_depth=self.door_depth,
                hinge_side=self.hinge_side,
                opening_side=self.opening_side,
                auto_texture=self.parent_widget.auto_texture)
            return creator.create()
        except ValueError as e:
            LOGGER.debug(e)
            return False
