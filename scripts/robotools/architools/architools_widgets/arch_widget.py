from __future__ import annotations

import contextlib
import logging
from PySide6.QtCore import QSettings

import robotools
from core import DEVELOPER
from robotools import CustomType
from core import logging_utils
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from robotools.architools import arch_utils, TOOL_NAME, ARCHITOOLS_COLOR
from robotools.anchor import Anchor
from robotools.boxy import boxy_utils
from robotools.boxy.boxy_data import BoxyData
from core.point_classes import Point3

with contextlib.suppress(ImportError):
    from maya_tools import node_utils
    from maya import cmds

# All architypes that can be converted
ARCHITYPES = (CustomType.window, CustomType.door, CustomType.staircase)

LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)


class ArchWidget(GenericWidget):
    def __init__(self, custom_type: CustomType, parent=None):
        self.custom_type: CustomType = custom_type
        super().__init__(title=self.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self._info = None
        self.parent_widget = parent if parent else None
        self.form: FormWidget = self.add_widget(FormWidget(title=f"{self.title} Creator"))
        self.add_button(text=f"Generate {self.title}", clicked=self.generate_button_clicked,
                        tool_tip=f"Generate {self.title}")

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

    def generate_architype(self):
        """Convert boxy to CustomType geometry.

        - Override with construction logic.
        """
        pass

    def generate_button_clicked(self):
        """Event for create button.

        Processes all selected nodes:
        - Boxy nodes: convert directly to architype
        - Architype nodes (window, door, staircase): convert to boxy, then to target architype
        - Meshboxes: convert to boxy, then to architype
        """
        new_objects = []
        boxy_nodes = []

        try:
            # Phase 1: Pre-convert all selected nodes to boxy nodes
            selected_nodes = node_utils.get_selected_transforms(full_path=True)

            if not selected_nodes:
                # Nothing selected - create default boxy at origin
                size = self.parent_widget.default_cube_size if self.parent_widget else 100.0
                data = BoxyData(
                    size=Point3(size, size, size),
                    translation=Point3(0.0, 0.0, 0.0),
                    rotation=Point3(0.0, 0.0, 0.0),
                    pivot_anchor=Anchor.f2,
                    color=ARCHITOOLS_COLOR
                )
                boxy_node = boxy_utils.build(boxy_data=data)
                if boxy_node:
                    boxy_nodes.append(boxy_node)
            else:
                for node in selected_nodes:
                    if robotools.is_boxy(node):
                        boxy_nodes.append(node)
                    elif any(robotools.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                        boxy_node = arch_utils.convert_node_to_boxy(node=node, delete=True)
                        if boxy_node:
                            boxy_nodes.append(boxy_node)
                    elif robotools.is_meshbox(node) and boxy_utils.has_simple_topology(node):
                        boxy_node = boxy_utils.convert_meshbox_to_boxy(meshbox=node)
                        if boxy_node:
                            boxy_nodes.append(boxy_node)

            # Phase 2: Convert each boxy node to the target architype
            for boxy_node in boxy_nodes:
                if not cmds.objExists(boxy_node):
                    continue
                cmds.select(boxy_node, noExpand=True)
                result = self.generate_architype()
                if result:
                    new_objects.append(result)

            if new_objects:
                self.info = f"{self.title}(s) created: {len(new_objects)}"
            else:
                self.info = f"No {self.title}s created"

        except AssertionError as e:
            self.info = str(e)

        if new_objects:
            existing_objects = [obj for obj in new_objects if cmds.objExists(obj)]
            if existing_objects:
                cmds.select(existing_objects)
