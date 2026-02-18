"""App for creating procedural objects for Architools."""
from __future__ import annotations

import contextlib
import logging
import sys

import robotools
from core import DEVELOPER
from core.core_enums import Alignment, Side
from core.core_paths import image_path
from core.environment_utils import is_using_maya_python
from core.logging_utils import get_logger
from core.point_classes import Point3, ZERO3
from qtpy.QtCore import QSettings
from qtpy.QtWidgets import (
    QLabel, QTreeWidget, QLineEdit, QTreeWidgetItem
)
from robotools import CustomType
from robotools.anchor import Anchor
from robotools.architools import ARCHITOOLS_COLOR
from robotools.architools_studio import VERSIONS, TOOL_NAME
from robotools.architools_studio.size_widget import SizeWidget
from robotools.boxy import boxy_utils
from robotools.boxy.boxy_data import BoxyData
from robotools.boxy.meshbox_data import MeshboxData
from widgets.anchor_picker import AnchorPicker
from widgets.button_bar import ButtonBar
from widgets.float_array_widget import FloatArrayWidget
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.image_label import ImageLabel
from widgets.tag_widget import TagWidget, CaseMode, LayoutMode

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


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
        self.boxy_label = form.add_label(label="Boxy node:", default_value="")
        self.boxy_node = None
        self.add_stretch()

    @property
    def boxy_node(self):
        """Boxy node."""
        return self._boxy_node

    @boxy_node.setter
    def boxy_node(self, value):
        self._boxy_node = value
        self.boxy_label.setText(value if value else "None")



class MeshboxEditor(Editor):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.meshbox, parent_widget=parent_widget)
        self.node_label = self.add_label()
        self.node = parent_widget.current_tree_widget_item_text
        self.add_label("Pivot")
        self.pivot_picker: AnchorPicker = self.add_widget(AnchorPicker(advanced_mode=True))
        self.add_label("Anchor")
        self.anchor_picker: AnchorPicker = self.add_widget(AnchorPicker(advanced_mode=True))
        self.size_widget: SizeWidget = self.add_widget(SizeWidget())
        self.add_stretch()

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
        self.boxy_editor: BoxyEditor = self.add_widget(BoxyEditor(parent_widget=parent_widget))
        self.mesh_box_editor: MeshBoxEditor = self.add_widget(MeshboxEditor(parent_widget=parent_widget))
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
    pivot_key: str = "Pivot"
    size_key: str = "Size"
    default_size: Point3 = Point3(60.0, 60.0, 60.0)

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings: QSettings = QSettings(DEVELOPER, TOOL_NAME)
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
        self.add_meshbox_button = button_bar.add_icon_button(icon_path=image_path("add_meshbox.png"),
                                                             tool_tip="Add Meshbox",
                                                             clicked=self._on_meshbox_button_clicked)
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
        self.top_node_form: FormWidget = self.add_group_box(FormWidget(title="Top Node Details"))
        self.architype_name_line_edit: QLineEdit = self.top_node_form.add_line_edit(
            label="Node Name", placeholder_text="Name of node...")
        self.boxy_node_button, self.boxy_node_label = self.top_node_form.add_button(
            button_text="Link Boxy Node", label="None", clicked=self.on_link_boxy_button_clicked)
        new_node_form: FormWidget = self.add_group_box(FormWidget(title="New Node Attributes"))
        self.size_field: FloatArrayWidget = new_node_form.add_row(label=self.size_key, widget=FloatArrayWidget(
            count=3, default_value=50.0, minimum=0.0, maximum=1000.0, step=1.0))
        self.pivot_field: AnchorPicker = new_node_form.add_row(label=self.pivot_key,
                                                               widget=AnchorPicker(advanced_mode=True,
                                                                                   default=Anchor.f2))
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
        self.node_dict: dict = {}
        self.boxy_data = None
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
        boxy_data: BoxyData = BoxyData(
            size=self.size_value,
            translation=ZERO3,
            rotation=ZERO3,
            pivot_anchor=self.pivot_anchor,
            color=ARCHITOOLS_COLOR
        )
        if is_using_maya_python():
            boxy = boxy_utils.build(boxy_data=boxy_data)
        else:
            boxy = "boxy"
        self.node_dict[boxy] = boxy_data
        self.boxy_node_label.setText(boxy)

    def on_link_boxy_button_clicked(self):
        """Event for link_button."""
        self.info = "_on_connect_boxy_button_clicked"
        if is_using_maya_python():
            boxy_nodes = [x for x in node_utils.get_selected_transforms(full_path=True) if is_boxy(node=x)]
            if len(boxy_nodes) == 1:
                self.info = boxy_nodes[0]
                self.boxy_node = boxy_nodes[0]
                self.boxy_data = boxy_utils.get_boxy_data(self.boxy_node)
            else:
                self.info = "Select a single boxy node"
            # if not cmds.objExists(self.boxy_node):
            #     self.info = "Boxy widget not found."

    def _on_pivot_changed(self):
        """Event for pivot picker."""
        self.settings.setValue(self.pivot_key, self.pivot_field.selected_anchor.name)

    def _on_architype_name_line_edit_return_pressed(self):
        """Event for architype_name_line_edit."""
        if self.architype_name:
            self.info = f"Architype node: {self.architype_name}"
            self.top_node_label.setText(f"Architype node: {self.architype_name}")
        else:
            self.info = "Oopsie, no architype name"
        self._update_ui()

    def _on_meshbox_button_clicked(self):
        """Event for add_meshbox_button clicked."""
        data: MeshboxData = MeshboxData(size=self.size_value, pivot_anchor=self.pivot_anchor, translation=ZERO3,
                                        rotation=ZERO3)
        if is_using_maya_python():
            meshbox = boxy_utils.create_meshbox(pivot=self.pivot_anchor, size=self.size_value)
        else:
            meshbox = f"Meshbox{len(self.node_dict)}"
        # Add to meshboxes to dict
        self.node_dict[meshbox] = data
        # Add top-level item to tree widget
        meshbox_item = QTreeWidgetItem(self.tree_widget, [meshbox])
        self.tree_widget.addTopLevelItem(meshbox_item)
        self._update_ui()

    def _on_size_field_changed(self):
        """Event for size_field_changed."""
        LOGGER.debug(self.size_field.values)
        self.settings.setValue(self.size_key, self.size_field.values)

    def _on_tree_widget_item_clicked(self, *args):
        """Event for tree_widget item clicked."""
        text = args[0].text(0)
        self.info = text
        if is_using_maya_python() and cmds.objExists(text):
            if robotools.is_boxy(text):
                self.edit_panel.custom_type = CustomType.boxy
            elif robotools.is_meshbox(text):
                self.edit_panel.custom_type = CustomType.meshbox
            else:
                self.edit_panel.custom_type = None
        else:
            if "boxy" in text.lower():
                self.edit_panel.custom_type = CustomType.boxy
            elif "meshbox" in text:
                self.edit_panel.custom_type = CustomType.meshbox
            else:
                self.edit_panel.custom_type = None

    def _setup_ui(self):
        """Setup ui."""
        self.architype_name_line_edit.textChanged.connect(self._filter_architype_name)
        self.architype_name_line_edit.returnPressed.connect(self._on_architype_name_line_edit_return_pressed)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self._on_tree_widget_item_clicked)
        self.size_field.values = self.settings.value(self.size_key, self.default_size.values)
        self.size_field.value_changed.connect(self._on_size_field_changed)
        self.pivot_field.selected_anchor = self.default_anchor
        self.pivot_field.anchor_selected.connect(self._on_pivot_changed)
        self._update_ui()

    def _update_ui(self):
        """Update ui."""
        valid_architype_name = bool(self.architype_name)
        self.add_profile_button.setEnabled(valid_architype_name)
        self.add_constant_button.setEnabled(valid_architype_name)
        self.add_fixture_button.setEnabled(valid_architype_name)
        # Disable add_boxy button if boxy is already added
        # has_boxy = self.boxy_node and self.boxy_node != "None"
        # self.add_boxy_button.setEnabled(not has_boxy)

    @property
    def architype_name(self) -> str:
        """Text value of architype_name_line_edit."""
        return self.architype_name_line_edit.text()

    @property
    def boxy_data(self) -> BoxyData | None:
        return self._boxy_data

    @boxy_data.setter
    def boxy_data(self, value: BoxyData | None):
        self._boxy_data = value

    @property
    def boxy_node(self) -> str | None:
        return self._boxy_node

    @boxy_node.setter
    def boxy_node(self, value: str | None) -> None:
        self._boxy_node = value
        label = value if value else "[boxy]"
        if self.tree_widget.topLevelItemCount():
            self.tree_widget.topLevelItem(0).setText(0, label)
        else:
            tree_widget_item = QTreeWidgetItem(self.tree_widget, [label])
            self.tree_widget.addTopLevelItem(tree_widget_item)
        self.edit_panel.boxy_editor.boxy_node = value
        self.boxy_node_label.setText(value if value else "None")


    @property
    def current_tree_widget_item_text(self) -> str:
        """Text of the current_tree_widget_item."""
        return self.tree_widget.currentItem().text(0) if self.tree_widget.currentItem() else "None"

    @property
    def default_anchor(self) -> Anchor:
        return Anchor[self.settings.value(self.pivot_key)] if self.settings.value(self.pivot_key) else Anchor.f2

    @property
    def info(self) -> str:
        """Text value of the the info_label."""
        return self.info_label.text()

    @info.setter
    def info(self, value: str) -> None:
        self.info_label.setText(value)

    @property
    def pivot_anchor(self) -> Anchor:
        """Value of the pivot_anchor field."""
        return self.pivot_field.selected_anchor

    @property
    def size_value(self) -> Point3:
        """Value of the size field."""
        return Point3(*self.size_field.values)


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
    # print(_widget.pivot_anchor)
    sys.exit(app.exec())
