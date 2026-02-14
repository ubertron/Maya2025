"""App for creating procedural objects for Architools."""
from __future__ import annotations

import contextlib
import sys

from dataclasses import dataclass

from core.core_enums import Alignment, Side
from core.core_paths import image_path
from core.point_classes import Point3
from qtpy.QtWidgets import (
    QLabel, QTreeWidget, QLineEdit, QDialog, QTreeWidgetItem
)
from robotools import is_boxy
from robotools.anchor import Anchor
from robotools.architools_studio import VERSIONS
from widgets.button_bar import ButtonBar
from widgets.dimensions_dialog import DimensionsDialog
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.image_label import ImageLabel
from widgets.tag_widget import TagWidget, CaseMode, LayoutMode

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils


class ArchitoolsStudio(GenericWidget):
    """Main tool."""
    button_size: int = 32
    name_label: str = "Architype Node"

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        header: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        logo = header.add_widget(ImageLabel(path=image_path("architools_icon.png")))
        logo.setFixedSize(self.button_size, self.button_size)
        header_label: QLabel = header.add_label("architools studio", side=Side.left)
        header_label.setStyleSheet("font-size: 24pt; font-family: BM Dohyeon, Arial;")
        button_bar: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        button_bar.add_icon_button(icon_path=image_path("new.png"), tool_tip="New Architype")
        button_bar.add_icon_button(icon_path=image_path("open.png"), tool_tip="Open Architype")
        button_bar.add_icon_button(icon_path=image_path("save.png"), tool_tip="Save Architype")
        button_bar.add_icon_button(icon_path=image_path("curveEP.png"), tool_tip="Curve EP Tool")
        self.add_boxy_button = button_bar.add_icon_button(icon_path=image_path("add_boxy.png"), tool_tip="Add Boxy",
                                                          clicked=self._on_boxy_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("components.png"), tool_tip="Show components")
        self.add_polycube_button = button_bar.add_icon_button(icon_path=image_path("add_polycube.png"), tool_tip="Add Polycube",
                                                               clicked=self._on_add_polycube_button_clicked)
        self.add_constant_button = button_bar.add_icon_button(icon_path=image_path("add_constant.png"),
                                                              tool_tip="Add Constant")
        self.add_fixture_button = button_bar.add_icon_button(icon_path=image_path("add_fixture.png"),
                                                             tool_tip="Add Fixture")
        self.add_profile_button = button_bar.add_icon_button(icon_path=image_path("add_profile.png"),
                                                             tool_tip="Add Profile")
        button_bar.add_icon_button(icon_path=image_path("skin.png"), tool_tip="Loft")
        button_bar.add_icon_button(icon_path=image_path("lock_cvs.png"), tool_tip="Lock cvs to components")
        self.document_label: QLabel = self.add_label("Current document: None", side=Side.left)
        button_bar.add_stretch()
        button_bar.add_icon_button(icon_path=image_path("help.png"))
        self.form: FormWidget = self.add_group_box(FormWidget(title="Architype Attributes"))
        self.architype_name_line_edit: QLineEdit = self.form.add_line_edit(label="Name",
                                                                           placeholder_text="Name of node...")
        # self.connect_boxy_button, self.boxy_label = self.form.add_button(button_text="Connect Boxy", label="None",
        #                                                                  clicked=self._on_connect_boxy_button_clicked,
        #                                                                  tool_tip="Connect Boxy")
        content = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        column0 = content.add_widget(GenericWidget())
        self.top_node_label: QLabel = column0.add_label("Architype Node: None", side=Side.left)
        self.tree_widget: QTreeWidget = column0.add_widget(QTreeWidget())
        self.details_panel: GenericWidget = content.add_widget(GenericWidget())
        self.tag_widget: TagWidget = self.add_group_box(
            TagWidget(title="Tags", case_mode=CaseMode.lower, layout_mode=LayoutMode.scroll, allow_numbers=True,
                      special_characters="_", place_holder_text="Enter descriptive tags...",
                      comma_separation_mode=True))
        self.info_label: QLabel = self.add_label("Ready...", side=Side.left)
        self.polycubes: list[str] = []
        self.boxy_node = None
        self._setup_ui()

    def _filter_architype_name(self, text: str):
        """Filter architype name input.

        Rules:
        - First character must be a letter
        - All uppercase converted to lowercase
        - Spaces and special characters (except "_") converted to "_"
        - No numbers allowed
        - Leading/trailing whitespace stripped
        """
        if not text:
            return

        # Strip leading/trailing whitespace
        text = text.strip()

        filtered = []
        for i, char in enumerate(text):
            if char.isalpha():
                filtered.append(char.lower())
            elif char == "_" and i > 0:
                filtered.append(char)
            elif not char.isalnum() and i > 0:
                # Convert spaces and special chars to underscore
                filtered.append("_")
            # Numbers and invalid first chars are simply skipped

        filtered_text = "".join(filtered)

        # Only update if different to avoid infinite recursion
        if filtered_text != text:
            self.architype_name_line_edit.blockSignals(True)
            self.architype_name_line_edit.setText(filtered_text)
            self.architype_name_line_edit.blockSignals(False)

    def _on_connect_boxy_button_clicked(self):
        """Event for connect_boxy_button."""
        self.info = "_on_connect_boxy_button_clicked"
        boxy_nodes = [x for x in node_utils.get_selected_transforms(full_path=True) if is_boxy(node=x)]
        if len(boxy_nodes) == 1:
            self.boxy_label.setText(boxy_nodes[0])
        else:
            self.info = "Select a single boxy node"
        if not cmds.objExists(self.boxy_node):
            self.boxy_label.setText("None")

    def _on_boxy_button_clicked(self):
        """Event for add_boxy_button clicked."""
        dialog = DimensionsDialog(parent=self, title="Add Boxy")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            width, height, depth = dialog.dimensions
            self.info = f"Boxy dimensions: Width={width}, Height={height}, Depth={depth}"
            # Add top-level item to tree widget
            # boxy_item = QTreeWidgetItem(self.tree_widget, ["boxy"])
            # self.tree_widget.addTopLevelItem(boxy_item)

            '''
            this bit happens in the connect boxy button event
            # Populate boxy label
            self.boxy_node = "boxy"
            '''
            self._update_ui()

    def _on_add_polycube_button_clicked(self):
        """Event for add_polycube_button clicked."""
        dialog = DimensionsDialog(parent=self, title="Add Polycube")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            width, height, depth = dialog.dimensions
            self.info = f"Polycube dimensions: Width={width}, Height={height}, Depth={depth}"
            # Generate polycube name
            polycube_name = f"Polycube{len(self.polycubes)}: -"
            # Add to polycubes list
            self.polycubes.append(polycube_name)
            # Add top-level item to tree widget
            polycube_item = QTreeWidgetItem(self.tree_widget, [polycube_name])
            self.tree_widget.addTopLevelItem(polycube_item)
            self._update_ui()

    def _on_architype_name_line_edit_return_pressed(self):
        """Event for architype_name_line_edit."""
        if self.architype_name:
            self.info = f"Architype node: {self.architype_name}"
            self.top_node_label.setText(f"Architype node: {self.architype_name}")
        else:
            self.info = "Oopsie, no architype name"
        self._update_ui()

    def _on_tree_widget_item_clicked(self, *args):
        """Event for tree_widget item clicked."""
        self.info = str(args)


    def _setup_ui(self):
        """Setup ui."""
        self.architype_name_line_edit.textChanged.connect(self._filter_architype_name)
        self.architype_name_line_edit.returnPressed.connect(self._on_architype_name_line_edit_return_pressed)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self._on_tree_widget_item_clicked)
        self._update_ui()

    def _update_ui(self):
        """Update ui."""
        valid_architype_name = bool(self.architype_name)
        self.add_profile_button.setEnabled(valid_architype_name)
        self.add_constant_button.setEnabled(valid_architype_name)
        self.add_fixture_button.setEnabled(valid_architype_name)
        # Disable add_boxy button if boxy is already added
        has_boxy = self.boxy_node and self.boxy_node != "None"
        self.add_boxy_button.setEnabled(not has_boxy)

    @property
    def architype_name(self) -> str:
        """Text value of architype_name_line_edit."""
        return self.architype_name_line_edit.text()

    @property
    def info(self) -> str:
        """Text value of the the info_label."""
        return self.info_label.text()

    @info.setter
    def info(self, value: str) -> None:
        self.info_label.setText(value)

    @property
    def boxy_node(self) -> str | None:
        return self._boxy_node

    @boxy_node.setter
    def boxy_node(self, value: str | None) -> None:
        self._boxy_node = value
        label = f"Boxy node: {value if value else 'None'}"
        if self.tree_widget.topLevelItemCount():
            self.tree_widget.topLevelItem(0).setText(0, label)
        else:
            tree_widget_item =  QTreeWidgetItem(self.tree_widget, [label])
            self.tree_widget.addTopLevelItem(tree_widget_item)


@dataclass
class PolycubeData:
    size: Point3
    pivot: Anchor
    anchor: Anchor
    translation: Point3
    rotation: Point3
    scale: Point3


def launch():
    """Launch ArchitoolsStudio."""
    from maya_tools.maya_widget_utils import launch_tool
    launch_tool(
        tool_module="robotools.architools_studio.architools_studio", tool_class="ArchitoolsStudio",
        use_workspace_control=True,
        ui_script="from robotools.architools_studio import architools_studio; architools_studio.ArchitoolsStudio().restore()")


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = ArchitoolsStudio()
    widget.show()
    sys.exit(app.exec())
