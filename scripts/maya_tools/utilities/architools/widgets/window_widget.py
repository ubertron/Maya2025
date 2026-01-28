from __future__ import annotations

import logging

from PySide6.QtWidgets import QDoubleSpinBox

from maya import cmds

from core.core_enums import CustomType
from core.logging_utils import get_logger
from maya_tools import node_utils
from maya_tools.utilities.architools import window_creator
from maya_tools.utilities.architools.widgets.arch_widget import ArchWidget
from maya_tools.utilities.boxy import boxy_utils

LOGGER = get_logger(__name__, level=logging.DEBUG)


class WindowWidget(ArchWidget):
    sill_thickness_key = "sill_thickness"
    sill_depth_key = "sill_depth"
    frame_key = "frame"
    skirt_key = "skirt"

    def __init__(self, parent=None):
        super().__init__(custom_type=CustomType.window, parent=parent)
        default_sill_thickness = self.settings.value(self.sill_thickness_key, 2.0)
        default_sill_depth = self.settings.value(self.sill_depth_key, 5.0)
        default_frame = self.settings.value(self.frame_key, 10.0)
        default_skirt = self.settings.value(self.skirt_key, 2.0)
        self.sill_thickness_input: QDoubleSpinBox = self.form.add_float_field(
            label="Sill Thickness", default_value=default_sill_thickness, minimum=0.2, maximum=10.0, step=1.0)
        self.sill_depth_input: QDoubleSpinBox = self.form.add_float_field(
            label="Sill Depth", default_value=default_sill_depth, minimum=0.0, maximum=50.0, step=1.0)
        self.frame_input: QDoubleSpinBox = self.form.add_float_field(
            label="Frame Size", default_value=default_frame, minimum=1.0, maximum=50.0, step=1.0)
        self.skirt_input: QDoubleSpinBox = self.form.add_float_field(
            label="Skirt Size", default_value=default_skirt, minimum=0.5, maximum=5.0, step=0.1)
        self._setup_ui()

    def _setup_ui(self):
        """Setup events."""
        self.sill_thickness_input.valueChanged.connect(lambda: self.settings.setValue(self.sill_thickness_key, self.sill_thickness))
        self.sill_depth_input.valueChanged.connect(lambda: self.settings.setValue(self.sill_depth_key, self.sill_depth))
        self.frame_input.valueChanged.connect(lambda: self.settings.setValue(self.frame_key, self.frame))
        self.skirt_input.valueChanged.connect(lambda: self.settings.setValue(self.skirt_key, self.skirt))

    @property
    def sill_depth(self) -> float:
        return self.sill_depth_input.value()

    @property
    def sill_thickness(self) -> float:
        return self.sill_thickness_input.value()

    @property
    def frame(self) -> float:
        return self.frame_input.value()

    @property
    def skirt(self) -> float:
        return self.skirt_input.value()

    def convert_boxy(self) -> str | False:
        try:
            position = None
            boxy_node = next((iter(boxy_utils.get_selected_boxy_nodes())), None)
            if boxy_node:
                position = node_utils.get_translation(boxy_node, absolute=True)
            creator = window_creator.WindowCreator(
                sill_depth=self.sill_depth,
                sill_thickness=self.sill_thickness,
                frame=self. frame,
                skirt=self.skirt,
                auto_texture=self.parent_widget.auto_texture
            )
            result = creator.create()
            LOGGER.debug(f">>> setting position to {position}")
            node_utils.set_translation(result, value=position, absolute=True)
            return result
        except (ValueError, AssertionError) as e:
            LOGGER.debug(e)
            return False
