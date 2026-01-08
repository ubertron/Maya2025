from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox

from maya import cmds

from core.core_enums import CustomType
from maya_tools.utilities.architools import staircase_creator
from maya_tools.utilities.architools.widgets.arch_widget import ArchWidget


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
            creator = staircase_creator.StaircaseCreator(
                target_rise=self.target_rise,
                auto_texture=self.parent_widget.auto_texture)
            return creator.create()
        except ValueError as e:
            LOGGER.debug(e)
            return False
