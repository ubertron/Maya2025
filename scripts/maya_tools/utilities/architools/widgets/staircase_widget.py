from __future__ import annotations

import logging

from PySide6.QtWidgets import QDoubleSpinBox

from maya import cmds

from core.core_enums import CustomType
from core.logging_utils import get_logger
from maya_tools import node_utils
from maya_tools.utilities.architools import staircase_creator
from maya_tools.utilities.architools.widgets.arch_widget import ArchWidget
from maya_tools.utilities.boxy import boxy_utils

LOGGER = get_logger(__name__, level=logging.DEBUG)


class StaircaseWidget(ArchWidget):
    target_rise_key = "target_rise"

    def __init__(self, parent=None):
        super().__init__(custom_type=CustomType.staircase, parent=parent)
        default_target_rise = self.settings.value(self.target_rise_key, 20.0)
        self.rise_input: QDoubleSpinBox = self.form.add_float_field(
            label="Target rise", default_value=default_target_rise, minimum=1.0, maximum=200.0, step=1.0)
        self._setup_ui()

    def _setup_ui(self):
        """Setup events."""
        self.rise_input.valueChanged.connect(lambda: self.settings.setValue(self.target_rise))

    @property
    def target_rise(self) -> float:
        return self.rise_input.value()

    def convert_boxy(self) -> str | False:
        try:
            position = None
            boxy_node = next((iter(boxy_utils.get_selected_boxy_nodes())), None)
            if boxy_node:
                position = node_utils.get_translation(boxy_node, absolute=True)
            creator = staircase_creator.StaircaseCreator(
                target_rise=self.target_rise,
                auto_texture=self.parent_widget.auto_texture)
            result = creator.create()
            node_utils.set_translation(result, value=position, absolute=True)
            LOGGER.debug(f">>> setting position to {position}")
            return result
        except ValueError as e:
            LOGGER.debug(e)
            return False
