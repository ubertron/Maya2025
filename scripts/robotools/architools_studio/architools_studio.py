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
from robotools import is_boxy, CustomType
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


class Editor(GenericWidget):
    def __init__(self, custom_type: CustomType, parent_widget: GenericWidget):
        super().__init__(title=f"{custom_type.name.capitalize()} Editor")
        self.parent_widget = parent_widget
        self.custom_type = custom_type
        self.add_label(f"{custom_type.name.capitalize()} Editor")


class BoxyEditor(Editor):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.boxy, parent_widget=parent_widget)
        form: FormWidget = self.add_widget(FormWidget())
        form.add_button(button_text="Link", label="None", clicked=self._on_link_button_clicked)

    def _on_link_button_clicked(self):
        """Event for link_button."""
        self.parent_widget.info = "_on_connect_boxy_button_clicked"
        boxy_nodes = [x for x in node_utils.get_selected_transforms(full_path=True) if is_boxy(node=x)]
        if len(boxy_nodes) == 1:
            self.parent_widget.info = boxy_nodes[0]
        else:
            self.parent_widget.info = "Select a single boxy node"
        if not cmds.objExists(self.boxy_node):
            self.parent_widget.info = "Boxy widget not found."


class MeshboxEditor(Editor):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.meshbox, parent_widget=parent_widget)
        self.node_label = self.add_label()
        self.node = parent_widget.current_tree_widget_item_text

    def refresh(self):
        self.node = self.parent_widget.current_tree_widget_item_text

    @property
    def node(self) -> str:
        return self._node

    @node.setter
    def node(self, value: str):
        self._node = value
        self.node_label.setText(f"Node: {value}")



class EditPanel(GenericWidget):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(title="Edit Panel")
        self.add_widget(BoxyEditor(parent_widget=parent_widget))
        self.add_widget(MeshboxEditor(parent_widget=parent_widget))
        self.custom_type: CustomType | None = None

    @property
    def custom_type(self) -> CustomType | None:
        return self._custom_type

    @custom_type.setter
    def custom_type(self, value: CustomType | None):
        self._custom_type = value
        [widget.setVisible(widget.custom_type is value) for widget in self.widgets]
        widget = next((x for x in self.widgets if x.isVisible()), None)
        if widget:
            try:
                widget.refresh()
            except AttributeError:
                pass  # Widget doesn't have refresh method


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
        self.add_meshbox_button = button_bar.add_icon_button(icon_path=image_path("add_meshbox.png"), tool_tip="Add Meshbox",
                                                               clicked=self._on_add_meshbox_button_clicked)
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
        content = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        column0 = content.add_widget(GenericWidget())
        self.top_node_label: QLabel = column0.add_label("Architype Node: None", side=Side.left)
        self.tree_widget: QTreeWidget = column0.add_widget(QTreeWidget())
        self.edit_panel: EditPanel = content.add_widget(EditPanel(parent_widget=self))
        self.tag_widget: TagWidget = self.add_group_box(
            TagWidget(title="Tags", case_mode=CaseMode.lower, layout_mode=LayoutMode.scroll, allow_numbers=True,
                      special_characters="_", place_holder_text="Enter descriptive tags...",
                      separators=","))
        self.info_label: QLabel = self.add_label("Ready...", side=Side.left)
        self.meshboxes: list[str] = []
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

    def _on_boxy_button_clicked(self):
        """Event for add_boxy_button clicked."""
        dialog = DimensionsDialog(parent=self, title="Add Boxy")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            width, height, depth = dialog.dimensions
            self.info = f"Boxy dimensions: Width={width}, Height={height}, Depth={depth}"
            self._update_ui()

    def _on_add_meshbox_button_clicked(self):
        """Event for add_meshbox_button clicked."""
        dialog = DimensionsDialog(parent=self, title="Add Meshbox")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            width, height, depth = dialog.dimensions
            self.info = f"Meshbox dimensions: Width={width}, Height={height}, Depth={depth}"
            # Generate meshbox name
            meshbox_name = f"Meshbox{len(self.meshboxes)}: -"
            # Add to meshboxes list
            self.meshboxes.append(meshbox_name)
            # Add top-level item to tree widget
            meshbox_item = QTreeWidgetItem(self.tree_widget, [meshbox_name])
            self.tree_widget.addTopLevelItem(meshbox_item)
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
        text = args[0].text(0)
        self.info = text
        if "Boxy" in text:
            self.edit_panel.custom_type = CustomType.boxy
        elif "Meshbox" in text:
            self.edit_panel.custom_type = CustomType.meshbox
        else:
            self.edit_panel.custom_type = None

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

    @property
    def current_tree_widget_item_text(self) -> str:
        """Text of the current_tree_widget_item."""
        return self.tree_widget.currentItem().text(0) if self.tree_widget.currentItem() else "None"

@dataclass
class MeshboxData:
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
    _widget = ArchitoolsStudio()
    _widget.show()
    sys.exit(app.exec())
