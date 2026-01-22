from __future__ import annotations

from maya import cmds
from PySide6.QtCore import QSettings

from core import DEVELOPER
from core.core_enums import CustomType, Axis
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from maya_tools import node_utils
from maya_tools.utilities.architools import arch_utils, TOOL_NAME
from maya_tools.utilities.boxy import boxy_utils


class ArchWidget(GenericWidget):
    def __init__(self, custom_type: CustomType, parent=None):
        self.custom_type: CustomType = custom_type
        super().__init__(title=self.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self._info = None
        self.parent_widget = parent if parent else None
        self.form: FormWidget = self.add_widget(FormWidget(title=f"{self.title} Creator"))
        self.add_button(text=f"Generate {self.title}", clicked=self.create_button_clicked,
                        tool_tip=f"Generate {self.title}")
        self.add_button(text=f"Rotate {self.title} 90°", clicked=self.rotate_button_clicked,
                        tool_tip=f"Rotate {self.title}")
        self.add_button(text=f"Convert {self.title} To Boxy", clicked=self.convert_to_boxy_clicked,
                        tool_tip=f"Convert {self.title} To Boxy")

    @property
    def title(self):
        return self.custom_type.name.title()

    @property
    def info(self):
        return self.parent_widget.info if self.parent_widget else self._info

    @info.setter
    def info(self, value: str):
        if self.parent_widget and hasattr(self.parent_widget, "info"):
            self.parent_widget.info = value
        else:
            self._info = value

    def convert_to_boxy_clicked(self):
        """Event for convert boxy button."""
        self.info = "Convert To Boxy clicked"
        for node in arch_utils.get_custom_type(custom_type=self.custom_type, selected=True):
            arch_utils.convert_node_to_boxy(node=node, delete=True)

    def convert_boxy(self):
        """Convert boxy to CustomType geometry.

        - Override with construction logic.
        """
        pass

    def create_button_clicked(self):
        """Event for create button."""
        new_objects = []
        try:
            for node in arch_utils.get_custom_type(custom_type=self.custom_type, selected=True):
                arch_utils.convert_node_to_boxy(node=node, delete=True)
            node = self.convert_boxy()
            self.info = f"{self.title} created: {node}"
            if node:
                new_objects.append(node)
        except AssertionError as e:
            self.info = str(e)

        if new_objects:
            cmds.select(new_objects)

    def rotate_button_clicked(self):
        """Event for rotate button."""
        self.info = "Rotate button clicked"
        for x in node_utils.get_selected_transforms(full_path=True):
            if node_utils.is_custom_type(node=x, custom_type=self.custom_type):
                temp_boxy = arch_utils.convert_node_to_boxy(node=x, delete=True)
                boxy.edit_boxy_orientation(node=temp_boxy, rotation=-90, axis=Axis.y)
                self.convert_boxy()
            elif node_utils.is_boxy(x):
                boxy.edit_boxy_orientation(node=x, rotation=-90, axis=Axis.y)
