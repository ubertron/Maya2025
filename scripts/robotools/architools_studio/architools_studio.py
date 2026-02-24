"""App for creating procedural objects for Architools."""
from __future__ import annotations

import contextlib
import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.bounds import Bounds

import robotools
from core import DEVELOPER
from core.core_enums import Alignment, Side
from core.core_paths import image_path
from core.environment_utils import is_using_maya_python
from core.logging_utils import get_logger
from core.point_classes import Point3, ZERO3
from qtpy.QtCore import QSettings, Qt
from qtpy.QtWidgets import (
    QLabel, QTreeWidget, QLineEdit, QTreeWidgetItem, QFileDialog, QMenu, QDoubleSpinBox
)
from robotools.architools_studio.editors import BoxyEditor, MeshboxEditor, MirrorEditor, OffsetEditor, ParameterEditor

# Roles for storing data in tree widget items
NODE_ID_ROLE = Qt.UserRole + 1
IS_BOXY_ROLE = Qt.UserRole + 2  # True if this item represents the boxy node
from robotools import CustomType
from robotools.anchor import Anchor
from robotools.architools import ARCHITOOLS_COLOR
from robotools.architools_studio import VERSIONS, TOOL_NAME
from robotools.boxy import boxy_utils
from robotools.boxy.boxy_data import BoxyData
from robotools.architools_studio.nodes import (
    ArchitypeTemplate, MeshBoxNode, MirrorNode, OffsetNode, ParameterNode, SizeValue, SizeMode
)
from robotools.architools_studio import template_io
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


class EditPanel(GenericWidget):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(title="Edit Panel")
        self.boxy_editor: BoxyEditor = self.add_widget(BoxyEditor(parent_widget=parent_widget))
        self.mesh_box_editor: MeshBoxEditor = self.add_widget(MeshboxEditor(parent_widget=parent_widget))
        self.offset_editor: OffsetEditor = self.add_widget(OffsetEditor(parent_widget=parent_widget))
        self.mirror_editor: MirrorEditor = self.add_widget(MirrorEditor(parent_widget=parent_widget))
        self.parameter_editor: ParameterEditor = self.add_widget(ParameterEditor(parent_widget=parent_widget))
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
    default_boxy_size: Point3 = Point3(100.0, 100.0, 100.0)

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings: QSettings = QSettings(DEVELOPER, TOOL_NAME)
        self._template: ArchitypeTemplate = ArchitypeTemplate()
        self._selected_node_id: str | None = None
        self._modified: bool = False
        self._boxy_uuid: str | None = None  # Maya UUID for tracking linked boxy
        self._boxy_tree_item: QTreeWidgetItem | None = None  # Tree item for boxy node
        self._preview_uuids: list[str] = []  # Maya UUIDs for generated preview geometry

        header: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        logo = header.add_widget(ImageLabel(path=image_path("architools_icon.png")))
        logo.setFixedSize(self.button_size, self.button_size)
        header_label: QLabel = header.add_label("architools studio", side=Side.left)
        header_label.setStyleSheet("font-size: 24pt; font-family: BM Dohyeon, Arial;")
        button_bar: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        button_bar.add_icon_button(icon_path=image_path("new.png"), tool_tip="New Architype",
                                   clicked=self._on_new_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("open.png"), tool_tip="Open Architype",
                                   clicked=self._on_open_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("save.png"), tool_tip="Save Architype",
                                   clicked=self._on_save_button_clicked)
        self.create_boxy_button = button_bar.add_icon_button(icon_path=image_path("add_boxy.png"),
                                                              tool_tip="Create Boxy (and link)",
                                                              clicked=self._on_create_boxy_clicked)
        self.add_meshbox_button = button_bar.add_icon_button(icon_path=image_path("add_meshbox.png"),
                                                             tool_tip="Add Meshbox",
                                                             clicked=self._on_meshbox_button_clicked)
        self.add_offset_button = button_bar.add_icon_button(icon_path=image_path("offset.png"),
                                                            tool_tip="Add Offset to selected MeshBox",
                                                            clicked=self._on_offset_button_clicked)
        self.add_mirror_button = button_bar.add_icon_button(icon_path=image_path("mirror.png"),
                                                            tool_tip="Add Mirror to selected MeshBox",
                                                            clicked=self._on_mirror_button_clicked)
        self.add_parameter_button = button_bar.add_icon_button(icon_path=image_path("parameter.png"),
                                                               tool_tip="Add Parameter",
                                                               clicked=self._on_parameter_button_clicked)
        self.rebuild_button = button_bar.add_icon_button(icon_path=image_path("rebuild.png"),
                                                         tool_tip="Rebuild (regenerate scene geometry)",
                                                         clicked=self._on_rebuild_clicked)
        button_bar.add_stretch()
        button_bar.add_icon_button(icon_path=image_path("help.png"))
        self.document_label: QLabel = self.add_label("Current document: None", side=Side.left)
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
        # Parameter sliders panel for live adjustment
        self.parameter_panel: FormWidget = self.add_group_box(FormWidget(title="Parameters"))
        self._parameter_sliders: dict[str, QDoubleSpinBox] = {}  # param_id -> slider widget
        self.info_label: QLabel = self.add_label("Ready...", side=Side.left)
        self._boxy_data: BoxyData | None = None
        self._boxy_node: str | None = None
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

    def on_link_boxy_button_clicked(self):
        """Link a selected boxy node as the reference for this architype."""
        if not is_using_maya_python():
            self.info = "Link Boxy requires Maya"
            return

        # Find selected boxy nodes
        selected = node_utils.get_selected_transforms(full_path=True)
        boxy_nodes = [x for x in selected if robotools.is_boxy(node=x)]

        if len(boxy_nodes) != 1:
            self.info = "Select a single boxy node"
            return

        boxy_node = boxy_nodes[0]

        # Unlink previous boxy if any
        if self._boxy_node and self._boxy_uuid:
            self._unlock_boxy_attributes()
            self._remove_boxy_from_tree()

        # Store the new boxy reference
        self._boxy_node = boxy_node
        self._boxy_uuid = cmds.ls(boxy_node, uuid=True)[0]
        self._boxy_data = boxy_utils.get_boxy_data(boxy_node)

        # Update UI with boxy info
        self.boxy_node_label.setText(boxy_node.split("|")[-1])

        # Add boxy to tree widget
        self._add_boxy_to_tree()

        # Lock boxy attributes in channel box
        self._lock_boxy_attributes()

        self.info = f"Linked: {boxy_node}"
        self._update_ui()

    def _validate_boxy_node(self) -> bool:
        """Validate that the linked boxy node still exists.

        Returns True if valid, False if missing/invalid.
        """
        if not self._boxy_uuid:
            return False

        if not is_using_maya_python():
            return True  # Can't validate outside Maya

        # Try to find node by UUID
        nodes = cmds.ls(self._boxy_uuid, long=True)
        if not nodes:
            self.info = "Linked boxy node no longer exists"
            self._clear_boxy_link()
            return False

        # Update node name in case it was renamed
        current_name = nodes[0]
        if current_name != self._boxy_node:
            self._boxy_node = current_name
            self.boxy_node_label.setText(current_name.split("|")[-1])

        return True

    def _lock_boxy_attributes(self):
        """Lock boxy size/transform attributes in channel box."""
        if not self._boxy_node or not is_using_maya_python():
            return

        if not cmds.objExists(self._boxy_node):
            return

        # Lock transform attributes
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
            try:
                cmds.setAttr(f"{self._boxy_node}.{attr}", lock=True)
            except RuntimeError:
                pass

        # Lock shape size attributes
        shape = cmds.listRelatives(self._boxy_node, shapes=True, type="boxyShape")
        if shape:
            for attr in ["sizeX", "sizeY", "sizeZ"]:
                try:
                    cmds.setAttr(f"{shape[0]}.{attr}", lock=True)
                except RuntimeError:
                    pass

    def _unlock_boxy_attributes(self):
        """Unlock boxy attributes when unlinking."""
        if not self._boxy_node or not is_using_maya_python():
            return

        if not cmds.objExists(self._boxy_node):
            return

        # Unlock transform attributes
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
            try:
                cmds.setAttr(f"{self._boxy_node}.{attr}", lock=False)
            except RuntimeError:
                pass

        # Unlock shape size attributes
        shape = cmds.listRelatives(self._boxy_node, shapes=True, type="boxyShape")
        if shape:
            for attr in ["sizeX", "sizeY", "sizeZ"]:
                try:
                    cmds.setAttr(f"{shape[0]}.{attr}", lock=False)
                except RuntimeError:
                    pass

    def _clear_boxy_link(self):
        """Clear the boxy link and reset UI."""
        self._unlock_boxy_attributes()
        self._remove_boxy_from_tree()
        self._boxy_node = None
        self._boxy_uuid = None
        self._boxy_data = None
        self.boxy_node_label.setText("None")
        self._update_ui()

    def _add_boxy_to_tree(self):
        """Add the boxy node to the top of the tree widget."""
        if not self._boxy_node:
            return

        boxy_name = self._boxy_node.split("|")[-1]

        # Create boxy tree item at top level
        self._boxy_tree_item = QTreeWidgetItem(self.tree_widget, [boxy_name])
        self._boxy_tree_item.setData(0, IS_BOXY_ROLE, True)
        self.tree_widget.insertTopLevelItem(0, self._boxy_tree_item)

        # Move any existing meshbox items to be children of boxy
        items_to_move = []
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item != self._boxy_tree_item:
                items_to_move.append(item)

        for item in items_to_move:
            index = self.tree_widget.indexOfTopLevelItem(item)
            self.tree_widget.takeTopLevelItem(index)
            self._boxy_tree_item.addChild(item)

        # Expand boxy to show children
        self._boxy_tree_item.setExpanded(True)

    def _remove_boxy_from_tree(self):
        """Remove the boxy node from the tree widget."""
        if not self._boxy_tree_item:
            return

        # Move children back to top level before removing boxy
        children = []
        for i in range(self._boxy_tree_item.childCount()):
            children.append(self._boxy_tree_item.child(i))

        for child in children:
            self._boxy_tree_item.removeChild(child)
            self.tree_widget.addTopLevelItem(child)

        # Remove boxy item
        index = self.tree_widget.indexOfTopLevelItem(self._boxy_tree_item)
        if index >= 0:
            self.tree_widget.takeTopLevelItem(index)

        self._boxy_tree_item = None

    def _on_create_boxy_clicked(self):
        """Create a new boxy node and auto-link it."""
        if not is_using_maya_python():
            self.info = "Create Boxy requires Maya"
            return

        # Unlink previous boxy if any
        if self._boxy_node and self._boxy_uuid:
            self._unlock_boxy_attributes()
            self._remove_boxy_from_tree()

        # Create boxy with default size
        boxy_data = BoxyData(
            size=self.default_boxy_size,
            translation=ZERO3,
            rotation=ZERO3,
            pivot_anchor=self.pivot_anchor,
            color=ARCHITOOLS_COLOR
        )
        boxy_node = boxy_utils.build(boxy_data=boxy_data)

        # Link the new boxy
        self._boxy_node = boxy_node
        self._boxy_uuid = cmds.ls(boxy_node, uuid=True)[0]
        self._boxy_data = boxy_data

        # Update UI
        self.boxy_node_label.setText(boxy_node.split("|")[-1])

        # Add boxy to tree widget
        self._add_boxy_to_tree()

        # Lock attributes
        self._lock_boxy_attributes()

        self.info = f"Created and linked: {boxy_node}"
        self._update_ui()

    def rebuild_single_meshbox(self, node: MeshBoxNode):
        """Rebuild a single meshbox with updated size/position."""
        if not is_using_maya_python():
            return

        if not self._boxy_node or not self._validate_boxy_node():
            self.info = "Link a boxy node first"
            return

        # Delete existing Maya node if it exists
        if node.maya_uuid:
            maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
            if maya_node:
                try:
                    cmds.delete(maya_node)
                except RuntimeError:
                    pass
            if node.maya_uuid in self._preview_uuids:
                self._preview_uuids.remove(node.maya_uuid)
            node.maya_uuid = None

        # Delete mirror geometry if it exists
        for mirror_uuid in node.mirror_uuids:
            mirror_node = self.get_maya_node_from_uuid(mirror_uuid)
            if mirror_node:
                try:
                    cmds.delete(mirror_node)
                except RuntimeError:
                    pass
            if mirror_uuid in self._preview_uuids:
                self._preview_uuids.remove(mirror_uuid)
        node.mirror_uuids.clear()

        # Rebuild with current settings
        boxy_data = boxy_utils.get_boxy_data(self._boxy_node)
        boxy_bounds = boxy_utils.get_boxy_bounds(self._boxy_node)

        self._build_meshbox_from_node(node, boxy_data, boxy_bounds)
        self.info = f"Rebuilt: {node.name}"

    def _on_rebuild_clicked(self):
        """Rebuild all geometry from template data."""
        if not is_using_maya_python():
            self.info = "Rebuild requires Maya"
            return

        if not self._validate_boxy_node():
            self.info = "Link a boxy node first"
            return

        # Clear existing preview geometry
        self._clear_preview_geometry()

        # Get boxy data and bounds for positioning
        boxy_data = boxy_utils.get_boxy_data(self._boxy_node)
        boxy_bounds = boxy_utils.get_boxy_bounds(self._boxy_node)
        if not boxy_bounds:
            self.info = "Could not get boxy bounds"
            return

        # Build each MeshBox node
        created_count = 0
        for node in self._template.get_root_nodes():
            if isinstance(node, MeshBoxNode):
                maya_node = self._build_meshbox_from_node(node, boxy_data, boxy_bounds)
                if maya_node:
                    created_count += 1

        self.info = f"Rebuilt {created_count} meshbox(es)"

    def _build_meshbox_from_node(self, node: MeshBoxNode, boxy_data: BoxyData, boxy_bounds: Bounds) -> str | None:
        """Build a Maya meshbox from a MeshBoxNode definition."""
        from robotools import anchor_utils

        # Evaluate size values - pass node and bounds for lock mode calculations
        width = self._evaluate_size_value(node.width, boxy_data.size.x, "x", boxy_data, boxy_bounds, node)
        height = self._evaluate_size_value(node.height, boxy_data.size.y, "y", boxy_data, boxy_bounds, node)
        depth = self._evaluate_size_value(node.depth, boxy_data.size.z, "z", boxy_data, boxy_bounds, node)
        size = Point3(width, height, depth)

        # Create the meshbox
        meshbox = boxy_utils.create_meshbox(pivot=node.pivot_anchor, size=size)

        # Get target position on boxy (where pivot should be)
        target_position = anchor_utils.get_anchor_position_from_bounds(
            boxy_bounds, node.position_anchor
        )

        # Get meshbox pivot in local space and offset transform
        pivot_local = cmds.xform(meshbox, query=True, rotatePivot=True, objectSpace=True)
        transform_position = Point3(
            target_position.x - pivot_local[0],
            target_position.y - pivot_local[1],
            target_position.z - pivot_local[2]
        )

        # Move so pivot lands at target
        cmds.xform(meshbox, translation=transform_position.values, worldSpace=True)

        # Apply offset modifiers from child nodes
        self._apply_offsets(meshbox, node)

        # Rename to match node name - Maya returns actual name
        meshbox = cmds.rename(meshbox, node.name)
        actual_name = meshbox.split("|")[-1]

        # Store UUID for tracking in both node and preview list
        uuid = cmds.ls(meshbox, uuid=True)[0]
        node.maya_uuid = uuid
        node.name = actual_name  # Update node name with Maya's actual name
        self._preview_uuids.append(uuid)

        # Apply mirror modifiers (creates duplicate geometry)
        self._apply_mirror(meshbox, node, boxy_bounds)

        # Update tree widget to reflect actual name
        self.update_tree_item_name(node.id, actual_name)

        return meshbox

    def _apply_offsets(self, maya_node: str, node: MeshBoxNode) -> None:
        """Apply cumulative offset from all OffsetNode children.

        Args:
            maya_node: Maya transform node name
            node: MeshBoxNode with children list
        """
        total_offset = Point3(0.0, 0.0, 0.0)

        for child_id in node.children:
            child_node = self._template.get_node(child_id)
            if isinstance(child_node, OffsetNode):
                total_offset = Point3(
                    total_offset.x + child_node.offset_x,
                    total_offset.y + child_node.offset_y,
                    total_offset.z + child_node.offset_z
                )

        if total_offset.x != 0.0 or total_offset.y != 0.0 or total_offset.z != 0.0:
            # Get current position and add offset
            current_pos = cmds.xform(maya_node, query=True, translation=True, worldSpace=True)
            new_pos = [
                current_pos[0] + total_offset.x,
                current_pos[1] + total_offset.y,
                current_pos[2] + total_offset.z
            ]
            cmds.xform(maya_node, translation=new_pos, worldSpace=True)

    def _apply_mirror(self, maya_node: str, node: MeshBoxNode, boxy_bounds: "Bounds") -> list[str]:
        """Apply mirror modifiers to create duplicate geometry.

        Creates duplicates of the meshbox mirrored across the boxy center
        on X and/or Z axes based on MirrorNode children.

        Args:
            maya_node: Maya transform node name (source geometry)
            node: MeshBoxNode with children list
            boxy_bounds: Bounds of the boxy for calculating mirror center

        Returns:
            List of created Maya node names (duplicates only, not original)
        """
        created_nodes = []

        # Find mirror nodes in children
        mirror_x = False
        mirror_z = False
        for child_id in node.children:
            child_node = self._template.get_node(child_id)
            if isinstance(child_node, MirrorNode):
                mirror_x = mirror_x or child_node.mirror_x
                mirror_z = mirror_z or child_node.mirror_z

        if not mirror_x and not mirror_z:
            LOGGER.debug(f"=== Mirror: No mirror axes enabled for {maya_node} ===")
            return created_nodes

        # Get boxy center for mirroring
        boxy_center_x = boxy_bounds.position.x
        boxy_center_z = boxy_bounds.position.z

        # Get original position
        orig_pos = cmds.xform(maya_node, query=True, translation=True, worldSpace=True)

        LOGGER.debug(f"=== Mirror Debug for {maya_node} ===")
        LOGGER.debug(f"  mirror_x={mirror_x}, mirror_z={mirror_z}")
        LOGGER.debug(f"  boxy_bounds.position: ({boxy_bounds.position.x}, {boxy_bounds.position.y}, {boxy_bounds.position.z})")
        LOGGER.debug(f"  boxy_bounds.size: ({boxy_bounds.size.x}, {boxy_bounds.size.y}, {boxy_bounds.size.z})")
        LOGGER.debug(f"  boxy_center_x={boxy_center_x}, boxy_center_z={boxy_center_z}")
        LOGGER.debug(f"  orig_pos: {orig_pos}")

        # Create mirrors based on settings
        if mirror_x:
            # Mirror across X axis
            x_mirrored = cmds.duplicate(maya_node, name=f"{maya_node}_mirrorX")[0]
            new_x = 2 * boxy_center_x - orig_pos[0]
            LOGGER.debug(f"  X mirror: new_x = 2 * {boxy_center_x} - {orig_pos[0]} = {new_x}")
            cmds.xform(x_mirrored, translation=[new_x, orig_pos[1], orig_pos[2]], worldSpace=True)
            # Flip scale on X to mirror geometry
            cmds.setAttr(f"{x_mirrored}.scaleX", -1)
            created_nodes.append(x_mirrored)
            # Track UUID on node and preview list
            uuid = cmds.ls(x_mirrored, uuid=True)[0]
            node.mirror_uuids.append(uuid)
            self._preview_uuids.append(uuid)

        if mirror_z:
            # Mirror across Z axis
            z_mirrored = cmds.duplicate(maya_node, name=f"{maya_node}_mirrorZ")[0]
            new_z = 2 * boxy_center_z - orig_pos[2]
            LOGGER.debug(f"  Z mirror: new_z = 2 * {boxy_center_z} - {orig_pos[2]} = {new_z}")
            cmds.xform(z_mirrored, translation=[orig_pos[0], orig_pos[1], new_z], worldSpace=True)
            # Flip scale on Z to mirror geometry
            cmds.setAttr(f"{z_mirrored}.scaleZ", -1)
            created_nodes.append(z_mirrored)
            # Track UUID on node and preview list
            uuid = cmds.ls(z_mirrored, uuid=True)[0]
            node.mirror_uuids.append(uuid)
            self._preview_uuids.append(uuid)

        if mirror_x and mirror_z:
            # Diagonal mirror (both X and Z)
            xz_mirrored = cmds.duplicate(maya_node, name=f"{maya_node}_mirrorXZ")[0]
            new_x = 2 * boxy_center_x - orig_pos[0]
            new_z = 2 * boxy_center_z - orig_pos[2]
            LOGGER.debug(f"  XZ mirror: new_x={new_x}, new_z={new_z}")
            cmds.xform(xz_mirrored, translation=[new_x, orig_pos[1], new_z], worldSpace=True)
            # Flip scale on both X and Z
            cmds.setAttr(f"{xz_mirrored}.scaleX", -1)
            cmds.setAttr(f"{xz_mirrored}.scaleZ", -1)
            created_nodes.append(xz_mirrored)
            # Track UUID on node and preview list
            uuid = cmds.ls(xz_mirrored, uuid=True)[0]
            node.mirror_uuids.append(uuid)
            self._preview_uuids.append(uuid)

        LOGGER.debug(f"  Created {len(created_nodes)} mirror copies")
        LOGGER.debug(f"=== End Mirror Debug ===")

        return created_nodes

    def _evaluate_size_value(
        self, size_value: SizeValue, boxy_dimension: float,
        axis: str = "x", boxy_data: BoxyData = None, boxy_bounds: "Bounds" = None,
        current_node: MeshBoxNode = None, evaluating: set = None
    ) -> float:
        """Evaluate a SizeValue to get the actual dimension.

        For lock modes (min/center/max), scales the meshbox from its pivot so that
        the closer face reaches the target point. The pivot stays fixed, and the
        geometry scales symmetrically around it.

        Args:
            size_value: The SizeValue to evaluate.
            boxy_dimension: The boxy dimension for this axis (fallback).
            axis: Which axis this is for ("x", "y", or "z").
            boxy_data: BoxyData for resolving lock values.
            boxy_bounds: Bounds of the boxy for position calculations.
            current_node: The MeshBoxNode being built (needed for lock calculations).
            evaluating: Set of node IDs currently being evaluated (cycle detection).
        """
        from robotools import anchor_utils

        if size_value.mode == SizeMode.constant:
            if isinstance(size_value.value, (int, float)):
                return float(size_value.value)
            # Handle parameter references (e.g., "$thickness")
            if isinstance(size_value.value, str) and size_value.value.startswith("$"):
                param_name = size_value.value[1:]  # Strip the '$' prefix
                return self._template.get_parameter_value(param_name, default=50.0)
            return 50.0

        # Lock modes: min, center, max
        if size_value.mode in (SizeMode.min, SizeMode.center, SizeMode.max):
            if not boxy_bounds or not current_node:
                return boxy_dimension

            # Get current node's pivot position on the boxy
            pivot_pos = anchor_utils.get_anchor_position_from_bounds(
                boxy_bounds, current_node.position_anchor
            )

            # Get axis index
            axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
            pivot_axis_pos = [pivot_pos.x, pivot_pos.y, pivot_pos.z][axis_idx]

            # Get pivot offset ratio for this axis (-0.5 to +0.5)
            # This tells us where the pivot is relative to geometry center
            pivot_offset = anchor_utils.get_anchor_offset(
                current_node.pivot_anchor, 0.5, 0.5, 0.5
            )
            pivot_ratio = [pivot_offset.x, pivot_offset.y, pivot_offset.z][axis_idx]

            # Get target position
            target_pos = self._get_lock_target_position(
                size_value, axis_idx, boxy_bounds, boxy_data, boxy_dimension,
                current_node, evaluating
            )

            # Calculate size needed to stretch from pivot to target
            return self._calculate_lock_size(pivot_axis_pos, target_pos, pivot_ratio)

        return 50.0

    def _get_lock_target_position(
        self, size_value: SizeValue, axis_idx: int, boxy_bounds: "Bounds",
        boxy_data: BoxyData, boxy_dimension: float, current_node: MeshBoxNode,
        evaluating: set
    ) -> float:
        """Get the target position for a lock mode."""
        from robotools import anchor_utils

        lock_node_id = size_value.lock_node_id
        axis = ["x", "y", "z"][axis_idx]

        if lock_node_id is None:
            # Lock to boxy
            boxy_size = [boxy_bounds.size.x, boxy_bounds.size.y, boxy_bounds.size.z][axis_idx]
            boxy_center = [boxy_bounds.position.x, boxy_bounds.position.y, boxy_bounds.position.z][axis_idx]

            if size_value.mode == SizeMode.min:
                return boxy_center - boxy_size / 2
            elif size_value.mode == SizeMode.center:
                return boxy_center
            else:  # max
                return boxy_center + boxy_size / 2

        # Lock to another meshbox node
        if evaluating is None:
            evaluating = set()
        if lock_node_id in evaluating:
            LOGGER.warning(f"Cycle detected while evaluating lock size: {lock_node_id}")
            return 0.0

        locked_node = self._template.get_node(lock_node_id)
        if not isinstance(locked_node, MeshBoxNode):
            return 0.0

        evaluating.add(lock_node_id)

        # Get locked node's pivot position
        locked_pivot_pos = anchor_utils.get_anchor_position_from_bounds(
            boxy_bounds, locked_node.position_anchor
        )
        locked_pivot_axis = [locked_pivot_pos.x, locked_pivot_pos.y, locked_pivot_pos.z][axis_idx]

        # Get locked node's size (recursively evaluate)
        if axis == "x":
            locked_size_value = locked_node.width
        elif axis == "y":
            locked_size_value = locked_node.height
        else:
            locked_size_value = locked_node.depth

        locked_size = self._evaluate_size_value(
            locked_size_value, boxy_dimension, axis, boxy_data, boxy_bounds,
            locked_node, evaluating
        )
        evaluating.discard(lock_node_id)

        # Get locked node's pivot ratio
        locked_pivot_offset = anchor_utils.get_anchor_offset(
            locked_node.pivot_anchor, 0.5, 0.5, 0.5
        )
        locked_pivot_ratio = [locked_pivot_offset.x, locked_pivot_offset.y, locked_pivot_offset.z][axis_idx]

        # Calculate locked node's geometry bounds
        # Center = pivot_pos - (pivot_ratio * size)
        locked_center = locked_pivot_axis - (locked_pivot_ratio * locked_size)
        locked_min = locked_center - locked_size / 2
        locked_max = locked_center + locked_size / 2

        if size_value.mode == SizeMode.min:
            return locked_min
        elif size_value.mode == SizeMode.center:
            return locked_center
        else:  # max
            return locked_max

    def _calculate_lock_size(self, pivot_pos: float, target_pos: float, pivot_ratio: float) -> float:
        """Calculate the size needed to scale from pivot to reach target.

        The meshbox scales from its pivot. The face closer to the target stretches
        to meet it. The pivot_ratio indicates where the pivot is relative to center:
        -0.5 = pivot at min edge, 0 = center, +0.5 = pivot at max edge.

        Args:
            pivot_pos: Position of the pivot on the axis.
            target_pos: Target position to reach.
            pivot_ratio: Pivot offset ratio (-0.5 to +0.5).

        Returns:
            The size needed on this axis.
        """
        if abs(target_pos - pivot_pos) < 0.0001:
            return 0.0

        if target_pos > pivot_pos:
            # Max face needs to stretch to reach target
            # max_face = pivot_pos + size * (0.5 - pivot_ratio)
            # So: size = (target - pivot) / (0.5 - pivot_ratio)
            coeff = 0.5 - pivot_ratio
            if coeff <= 0.0001:
                return 0.0  # Pivot is at max edge, can't stretch that way
            return (target_pos - pivot_pos) / coeff
        else:
            # Min face needs to stretch to reach target
            # min_face = pivot_pos - size * (0.5 + pivot_ratio)
            # So: size = (pivot - target) / (0.5 + pivot_ratio)
            coeff = 0.5 + pivot_ratio
            if coeff <= 0.0001:
                return 0.0  # Pivot is at min edge, can't stretch that way
            return (pivot_pos - target_pos) / coeff

    def _clear_preview_geometry(self):
        """Delete all preview geometry tracked by UUID."""
        if not is_using_maya_python():
            return

        for uuid in self._preview_uuids:
            nodes = cmds.ls(uuid, long=True)
            if nodes:
                try:
                    cmds.delete(nodes[0])
                except RuntimeError:
                    pass

        self._preview_uuids.clear()

    def update_tree_item_name(self, node_id: str, new_name: str):
        """Update the tree widget item text for a given node ID."""
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.data(0, NODE_ID_ROLE) == node_id:
                item.setText(0, new_name)
                return
            # Check children
            for j in range(item.childCount()):
                child = item.child(j)
                if child.data(0, NODE_ID_ROLE) == node_id:
                    child.setText(0, new_name)
                    return

    def get_maya_node_from_uuid(self, maya_uuid: str | None) -> str | None:
        """Get the current Maya node name from a stored UUID.

        Returns None if UUID is None or node no longer exists.
        """
        if not maya_uuid or not is_using_maya_python():
            return None
        nodes = cmds.ls(maya_uuid, long=True)
        return nodes[0] if nodes else None

    def rename_maya_node(self, node: MeshBoxNode, new_name: str) -> str:
        """Rename a Maya node and update the MeshBoxNode.

        Returns the actual name after rename (Maya may modify for uniqueness).
        """
        if not is_using_maya_python() or not node.maya_uuid:
            node.name = new_name
            return new_name

        maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
        if not maya_node:
            node.name = new_name
            return new_name

        # Rename in Maya and get actual result
        result = cmds.rename(maya_node, new_name)
        actual_name = result.split("|")[-1] if result else new_name
        node.name = actual_name
        return actual_name

    def update_maya_meshbox_pivot(self, node: MeshBoxNode):
        """Update a Maya meshbox's pivot position, keeping geometry in place."""
        if not is_using_maya_python() or not node.maya_uuid:
            return

        maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
        if not maya_node:
            return

        from robotools.anchor_utils import get_anchor_offset
        from maya_tools import node_utils

        # Get current pivot in object space (before change)
        old_pivot_local = cmds.xform(maya_node, query=True, rotatePivot=True, objectSpace=True)
        old_pivot_local = Point3(old_pivot_local[0], old_pivot_local[1], old_pivot_local[2])

        # Get current meshbox size from bounds
        bounds = cmds.exactWorldBoundingBox(maya_node)
        size_x = bounds[3] - bounds[0]
        size_y = bounds[4] - bounds[1]
        size_z = bounds[5] - bounds[2]

        # Calculate new pivot position (local offset from geometry center)
        hx, hy, hz = size_x / 2.0, size_y / 2.0, size_z / 2.0
        new_pivot_offset = get_anchor_offset(node.pivot_anchor, hx, hy, hz)

        # The geometry center in local space is at -old_pivot_local
        # (because the geometry was created centered, then pivot was offset)
        # New pivot in local space = geometry_center + new_pivot_offset
        #                          = -old_pivot_local + old_pivot_local + new_pivot_offset
        # Wait, that's not right either. Let me think differently.

        # Actually: the vertices are fixed in local space. The pivot can be anywhere.
        # We want to move the pivot from old_pivot_local to new_pivot_local
        # where new_pivot_local is relative to the geometry center.

        # Get geometry center in local space by querying bounding box in object space
        # Actually, let's use the world bbox center and convert to local
        world_center = Point3(
            (bounds[0] + bounds[3]) / 2.0,
            (bounds[1] + bounds[4]) / 2.0,
            (bounds[2] + bounds[5]) / 2.0
        )

        # Current transform position
        current_pos = node_utils.get_translation(maya_node)

        # Geometry center in local space = world_center - transform_pos
        local_center = Point3(
            world_center.x - current_pos.x,
            world_center.y - current_pos.y,
            world_center.z - current_pos.z
        )

        # New pivot in local space = local_center + new_pivot_offset
        new_pivot_local = Point3(
            local_center.x + new_pivot_offset.x,
            local_center.y + new_pivot_offset.y,
            local_center.z + new_pivot_offset.z
        )

        LOGGER.debug(f"=== update_maya_meshbox_pivot ===")
        LOGGER.debug(f"  old_pivot_local: {old_pivot_local}")
        LOGGER.debug(f"  world_center: {world_center}")
        LOGGER.debug(f"  current_pos: {current_pos}")
        LOGGER.debug(f"  local_center: {local_center}")
        LOGGER.debug(f"  new_pivot_offset: {new_pivot_offset}")
        LOGGER.debug(f"  new_pivot_local: {new_pivot_local}")

        # Set the new pivot in object space
        cmds.xform(maya_node, objectSpace=True, rotatePivot=new_pivot_local.values)
        cmds.xform(maya_node, objectSpace=True, scalePivot=new_pivot_local.values)

        # Adjust transform to keep geometry in place
        # pivot_world = transform + pivot_local
        # We want pivot to stay at same world position, but pivot_local changed
        # old_pivot_world = current_pos + old_pivot_local
        # new_pivot_world = new_pos + new_pivot_local
        # Set them equal: new_pos = current_pos + old_pivot_local - new_pivot_local
        adjusted_pos = Point3(
            current_pos.x + old_pivot_local.x - new_pivot_local.x,
            current_pos.y + old_pivot_local.y - new_pivot_local.y,
            current_pos.z + old_pivot_local.z - new_pivot_local.z
        )
        cmds.xform(maya_node, translation=adjusted_pos.values, worldSpace=True)

        LOGGER.debug(f"  adjusted_pos: {adjusted_pos}")
        LOGGER.debug(f"=== end update_maya_meshbox_pivot ===")

    def update_maya_meshbox_position(self, node: MeshBoxNode):
        """Update a Maya meshbox's position based on its position anchor on Boxy."""
        if not is_using_maya_python() or not node.maya_uuid:
            return

        maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
        if not maya_node or not self._boxy_node:
            return

        if not self._validate_boxy_node():
            return

        from robotools import anchor_utils
        from maya_tools import node_utils

        # Get position on boxy from bounds
        boxy_bounds = boxy_utils.get_boxy_bounds(self._boxy_node)
        target_position = anchor_utils.get_anchor_position_from_bounds(
            boxy_bounds, node.position_anchor
        )

        # Get meshbox pivot in local space
        pivot_local = cmds.xform(maya_node, query=True, rotatePivot=True, objectSpace=True)

        # To place the PIVOT at target_position, we need to offset the transform
        # World pivot = transform + local_pivot, so transform = target - local_pivot
        transform_position = Point3(
            target_position.x - pivot_local[0],
            target_position.y - pivot_local[1],
            target_position.z - pivot_local[2]
        )

        # Debug info
        LOGGER.debug(f"=== update_maya_meshbox_position ===")
        LOGGER.debug(f"  maya_node: {maya_node}")
        LOGGER.debug(f"  node.pivot_anchor: {node.pivot_anchor.name}")
        LOGGER.debug(f"  node.position_anchor: {node.position_anchor.name}")
        LOGGER.debug(f"  target_position (where pivot should be): {target_position}")
        LOGGER.debug(f"  pivot_local: {pivot_local}")
        LOGGER.debug(f"  transform_position (target - pivot): {transform_position}")

        # Move meshbox transform so pivot ends up at target
        cmds.xform(maya_node, translation=transform_position.values, worldSpace=True)

        # Verify
        final_pos = node_utils.get_translation(maya_node)
        world_pivot = Point3(final_pos.x + pivot_local[0], final_pos.y + pivot_local[1], final_pos.z + pivot_local[2])
        LOGGER.debug(f"  final transform pos: {final_pos}")
        LOGGER.debug(f"  world pivot pos: {world_pivot}")
        LOGGER.debug(f"=== end update_maya_meshbox_position ===")

    def update_all_meshbox_positions(self):
        """Update positions of all meshbox nodes based on current boxy size."""
        if not is_using_maya_python() or not self._boxy_node:
            return

        if not self._validate_boxy_node():
            return

        for node in self._template.get_root_nodes():
            if isinstance(node, MeshBoxNode):
                self.update_maya_meshbox_position(node)

    def update_boxy_size(self, new_size: list[float]):
        """Update boxy dimensions from editor.

        Args:
            new_size: List of [width, height, depth] values.
        """
        if not self._boxy_node or not is_using_maya_python():
            return

        if not self._validate_boxy_node():
            return

        size = Point3(*new_size)

        # Update the Maya boxy node
        shape = cmds.listRelatives(self._boxy_node, shapes=True, type="boxyShape")
        if shape:
            # Temporarily unlock for update
            for attr in ["sizeX", "sizeY", "sizeZ"]:
                cmds.setAttr(f"{shape[0]}.{attr}", lock=False)

            cmds.setAttr(f"{shape[0]}.sizeX", size.x)
            cmds.setAttr(f"{shape[0]}.sizeY", size.y)
            cmds.setAttr(f"{shape[0]}.sizeZ", size.z)

            # Re-lock
            for attr in ["sizeX", "sizeY", "sizeZ"]:
                cmds.setAttr(f"{shape[0]}.{attr}", lock=True)

        # Update stored data
        self._boxy_data = boxy_utils.get_boxy_data(self._boxy_node)

        # Update all meshbox positions and sizes to follow the new boxy size
        self._rebuild_all_meshboxes()

        self.info = f"Boxy resized to {size.x:.1f} x {size.y:.1f} x {size.z:.1f}"

    def update_boxy_pivot(self, new_pivot: Anchor):
        """Update boxy pivot from editor.

        This rebuilds the boxy node with the new pivot, keeping the visual
        geometry in the same position.

        Args:
            new_pivot: The new Anchor position for the pivot.
        """
        if not self._boxy_node or not is_using_maya_python():
            return

        if not self._validate_boxy_node():
            return

        # Get current boxy data before rebuild
        old_pivot = self._boxy_data.pivot_anchor

        if new_pivot == old_pivot:
            return  # No change

        # Rebuild boxy with new pivot (this preserves visual position)
        try:
            new_boxy = boxy_utils.rebuild(self._boxy_node, pivot=new_pivot)
            if isinstance(new_boxy, str):
                # Update our references
                self._boxy_node = new_boxy
                self._boxy_uuid = cmds.ls(new_boxy, uuid=True)[0]
                self._boxy_data = boxy_utils.get_boxy_data(new_boxy)

                # Update UI
                self.boxy_node_label.setText(new_boxy.split("|")[-1])
                if self._boxy_tree_item:
                    self._boxy_tree_item.setText(0, new_boxy.split("|")[-1])

                # Re-lock attributes
                self._lock_boxy_attributes()

                # Rebuild all meshboxes to follow new boxy
                self._rebuild_all_meshboxes()

                self.info = f"Boxy pivot changed to {new_pivot.name}"
            else:
                self.info = f"Failed to change pivot: {new_boxy}"
        except Exception as e:
            self.info = f"Error changing pivot: {e}"
            LOGGER.error(f"Failed to change boxy pivot: {e}")

    def _rebuild_all_meshboxes(self):
        """Rebuild all meshbox nodes based on current boxy."""
        if not is_using_maya_python() or not self._boxy_node:
            return

        for node in self._template.get_root_nodes():
            if isinstance(node, MeshBoxNode):
                self.rebuild_single_meshbox(node)

    def _on_pivot_changed(self):
        """Event for pivot picker."""
        self.settings.setValue(self.pivot_key, self.pivot_field.selected_anchor.name)

    def _on_architype_name_line_edit_return_pressed(self):
        """Event for architype_name_line_edit."""
        if self.architype_name:
            self._template.name = self.architype_name
            self.info = f"Architype node: {self.architype_name}"
            self.top_node_label.setText(f"Architype node: {self.architype_name}")
            self._modified = True
        else:
            self.info = "Oopsie, no architype name"
        self._update_ui()

    def _on_new_button_clicked(self):
        """Create a new empty template."""
        self._template = ArchitypeTemplate()
        self._selected_node_id = None
        self._modified = False
        self._clear_tree_widget()
        self._clear_boxy_link()
        self.architype_name_line_edit.setText("")
        self.top_node_label.setText("Architype node: None")
        self.document_label.setText("Current document: None")
        self.tag_widget.clear()
        self.info = "New template created"
        self._update_ui()

    def _on_open_button_clicked(self):
        """Open a template from JSON file."""
        architypes_folder = str(template_io.get_architypes_folder())
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Architype Template", architypes_folder,
            "JSON Files (*.json);;All Files (*)"
        )
        if not filepath:
            return

        try:
            self._template = template_io.load_template(filepath)
            self._selected_node_id = None
            self._modified = False
            self._rebuild_tree_widget()
            self.architype_name_line_edit.setText(self._template.name)
            self.top_node_label.setText(f"Architype node: {self._template.name}")
            self.document_label.setText(f"Current document: {filepath}")
            self.tag_widget.set_tags(self._template.tags)
            self.info = f"Loaded: {self._template.name}"
        except Exception as e:
            self.info = f"Error loading template: {e}"
            LOGGER.error(f"Failed to load template: {e}")

    def _on_save_button_clicked(self):
        """Save the current template to JSON file."""
        if not self._template.name or self._template.name == "untitled":
            self.info = "Please enter a template name first"
            return

        # Update template with current UI state
        self._template.tags = self.tag_widget.tags

        try:
            filepath = template_io.save_template(self._template)
            self._modified = False
            self.document_label.setText(f"Current document: {filepath}")
            self.info = f"Saved: {filepath}"
        except Exception as e:
            self.info = f"Error saving template: {e}"
            LOGGER.error(f"Failed to save template: {e}")

    def _clear_tree_widget(self):
        """Clear all items from the tree widget."""
        self.tree_widget.clear()

    def _rebuild_tree_widget(self):
        """Rebuild tree widget from template nodes."""
        self._clear_tree_widget()
        self._boxy_tree_item = None

        # Add boxy at top if linked
        if self._boxy_node:
            self._add_boxy_to_tree()

        # Add MeshBox nodes as children of boxy (or top-level if no boxy)
        for node in self._template.get_root_nodes():
            item = QTreeWidgetItem([node.name])
            item.setData(0, NODE_ID_ROLE, node.id)

            if self._boxy_tree_item:
                self._boxy_tree_item.addChild(item)
            else:
                self.tree_widget.addTopLevelItem(item)

            # Add child nodes (Offset, Mirror)
            for child in self._template.get_children(node.id):
                child_item = QTreeWidgetItem(item, [child.name])
                child_item.setData(0, NODE_ID_ROLE, child.id)

            # Expand meshbox items that have children
            if item.childCount() > 0:
                item.setExpanded(True)

        # Expand boxy to show children
        if self._boxy_tree_item:
            self._boxy_tree_item.setExpanded(True)

        # Add Parameter nodes at top level (separate from geometry hierarchy)
        for param in self._template.get_all_parameter_nodes():
            param_item = QTreeWidgetItem([f"${param.name}"])
            param_item.setData(0, NODE_ID_ROLE, param.id)
            self.tree_widget.addTopLevelItem(param_item)

        # Update parameter sliders panel
        self._update_parameter_sliders()

    def on_template_modified(self):
        """Called when template data is modified."""
        self._modified = True
        self.info = "Template modified"

    def _on_meshbox_button_clicked(self):
        """Event for add_meshbox_button clicked."""
        # Create Maya geometry first if in Maya - use returned name as source of truth
        desired_name = f"meshbox_{len(self._template)}"
        maya_uuid = None

        if is_using_maya_python():
            # Create meshbox with desired pivot and size
            meshbox = boxy_utils.create_meshbox(pivot=self.pivot_anchor, size=self.size_value)
            # Rename to our desired name - Maya returns the actual name (handles duplicates)
            meshbox = cmds.rename(meshbox, desired_name)
            # Store UUID for tracking
            maya_uuid = cmds.ls(meshbox, uuid=True)[0]
            # Use Maya's returned name (may differ if duplicate)
            actual_name = meshbox.split("|")[-1]

            # Position at boxy anchor if boxy is linked
            if self._boxy_node and self._validate_boxy_node():
                from robotools import anchor_utils
                boxy_bounds = boxy_utils.get_boxy_bounds(self._boxy_node)
                target_position = anchor_utils.get_anchor_position_from_bounds(
                    boxy_bounds, self.pivot_anchor
                )
                # Get meshbox pivot in local space
                pivot_local = cmds.xform(meshbox, query=True, rotatePivot=True, objectSpace=True)
                # Offset transform so pivot lands at target
                transform_position = Point3(
                    target_position.x - pivot_local[0],
                    target_position.y - pivot_local[1],
                    target_position.z - pivot_local[2]
                )
                LOGGER.debug(f"=== _on_meshbox_button_clicked positioning ===")
                LOGGER.debug(f"  meshbox: {meshbox}")
                LOGGER.debug(f"  pivot_anchor: {self.pivot_anchor.name}")
                LOGGER.debug(f"  target_position (where pivot should be): {target_position}")
                LOGGER.debug(f"  pivot_local: {pivot_local}")
                LOGGER.debug(f"  transform_position: {transform_position}")
                cmds.xform(meshbox, translation=transform_position.values, worldSpace=True)
                final_pos = cmds.xform(meshbox, query=True, translation=True, worldSpace=True)
                LOGGER.debug(f"  final transform pos: {final_pos}")
                LOGGER.debug(f"=== end positioning ===")
        else:
            actual_name = desired_name

        # Create MeshBoxNode in template with actual name
        meshbox_node = MeshBoxNode(
            name=actual_name,
            pivot_anchor=self.pivot_anchor,
            position_anchor=self.pivot_anchor,  # Default to same as pivot
            width=SizeValue.constant(self.size_value.x),
            height=SizeValue.constant(self.size_value.y),
            depth=SizeValue.constant(self.size_value.z),
            maya_uuid=maya_uuid,
        )
        self._template.add_node(meshbox_node)

        # Add to tree widget as child of boxy (or top level if no boxy)
        meshbox_item = QTreeWidgetItem([actual_name])
        meshbox_item.setData(0, NODE_ID_ROLE, meshbox_node.id)

        if self._boxy_tree_item:
            self._boxy_tree_item.addChild(meshbox_item)
            self._boxy_tree_item.setExpanded(True)
        else:
            self.tree_widget.addTopLevelItem(meshbox_item)

        # Select the new item
        self.tree_widget.setCurrentItem(meshbox_item)
        self._selected_node_id = meshbox_node.id
        self.edit_panel.custom_type = CustomType.meshbox

        self._modified = True
        self._update_ui()
        self.info = f"Created: {actual_name}"

    def _on_offset_button_clicked(self):
        """Add an offset modifier to the selected MeshBox node."""
        if not self._selected_node_id:
            self.info = "Select a MeshBox node first"
            return

        parent_node = self._template.get_node(self._selected_node_id)
        if not isinstance(parent_node, MeshBoxNode):
            self.info = "Select a MeshBox node first"
            return

        # Create OffsetNode as child of selected meshbox
        offset_node = OffsetNode(
            name=f"{parent_node.name}_offset",
            parent_id=parent_node.id,
            offset_x=0.0,
            offset_y=0.0,
            offset_z=0.0,
        )
        self._template.add_node(offset_node)
        parent_node.add_child(offset_node.id)

        # Find parent item in tree and add offset as child
        parent_item = self._find_tree_item_by_node_id(parent_node.id)
        if parent_item:
            offset_item = QTreeWidgetItem([offset_node.name])
            offset_item.setData(0, NODE_ID_ROLE, offset_node.id)
            parent_item.addChild(offset_item)
            parent_item.setExpanded(True)
            # Select the new offset item
            self.tree_widget.setCurrentItem(offset_item)
            self._selected_node_id = offset_node.id
            self.edit_panel.custom_type = CustomType.node_offset

        self._modified = True
        self._update_ui()
        self.info = f"Added offset to: {parent_node.name}"

    def _find_tree_item_by_node_id(self, node_id: str) -> QTreeWidgetItem | None:
        """Find a tree widget item by its node ID."""
        def search_children(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.data(0, NODE_ID_ROLE) == node_id:
                    return child
                result = search_children(child)
                if result:
                    return result
            return None

        # Search top-level items
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.data(0, NODE_ID_ROLE) == node_id:
                return item
            result = search_children(item)
            if result:
                return result
        return None

    def _on_mirror_button_clicked(self):
        """Add a mirror modifier to the selected MeshBox node."""
        if not self._selected_node_id:
            self.info = "Select a MeshBox node first"
            return

        parent_node = self._template.get_node(self._selected_node_id)
        if not isinstance(parent_node, MeshBoxNode):
            self.info = "Select a MeshBox node first"
            return

        # Check if meshbox already has a mirror node
        for child_id in parent_node.children:
            child_node = self._template.get_node(child_id)
            if isinstance(child_node, MirrorNode):
                self.info = "MeshBox already has a mirror modifier"
                return

        # Create MirrorNode as child of selected meshbox
        mirror_node = MirrorNode(
            name=f"{parent_node.name}_mirror",
            parent_id=parent_node.id,
            mirror_x=True,
            mirror_z=True,
        )
        self._template.add_node(mirror_node)
        parent_node.add_child(mirror_node.id)

        # Find parent item in tree and add mirror as child
        parent_item = self._find_tree_item_by_node_id(parent_node.id)
        if parent_item:
            mirror_item = QTreeWidgetItem([mirror_node.name])
            mirror_item.setData(0, NODE_ID_ROLE, mirror_node.id)
            parent_item.addChild(mirror_item)
            parent_item.setExpanded(True)
            # Select the new mirror item
            self.tree_widget.setCurrentItem(mirror_item)
            self._selected_node_id = mirror_node.id
            self.edit_panel.custom_type = CustomType.node_mirror

        # Rebuild to show mirrored geometry
        self.rebuild_single_meshbox(parent_node)

        self._modified = True
        self._update_ui()
        self.info = f"Added mirror to: {parent_node.name}"

    def _on_parameter_button_clicked(self):
        """Add a new parameter to the template."""
        # Generate unique parameter name
        existing_params = self._template.get_all_parameter_nodes()
        param_num = len(existing_params) + 1
        param_name = f"param{param_num}"

        # Create ParameterNode
        param_node = ParameterNode(
            name=param_name,
            default_value=10.0,
            min_value=1.0,
            max_value=100.0,
            step=1.0,
        )
        self._template.add_node(param_node)

        # Add to tree (at top level, not under boxy)
        param_item = QTreeWidgetItem([f"${param_name}"])
        param_item.setData(0, NODE_ID_ROLE, param_node.id)
        self.tree_widget.addTopLevelItem(param_item)

        # Select the new parameter
        self.tree_widget.setCurrentItem(param_item)
        self._selected_node_id = param_node.id
        self.edit_panel.custom_type = CustomType.node_parameter

        # Update parameter sliders panel
        self._update_parameter_sliders()

        self._modified = True
        self._update_ui()
        self.info = f"Added parameter: ${param_name}"

    def _on_size_field_changed(self):
        """Event for size_field_changed."""
        LOGGER.debug(self.size_field.values)
        self.settings.setValue(self.size_key, self.size_field.values)

    def _on_tree_widget_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Event for tree_widget item clicked."""
        is_boxy = item.data(0, IS_BOXY_ROLE)
        node_id = item.data(0, NODE_ID_ROLE)
        text = item.text(0)
        self.info = text

        if is_boxy:
            # Boxy node selected
            self._selected_node_id = None
            self.edit_panel.custom_type = CustomType.boxy
            # Update boxy editor with current boxy info
            self.edit_panel.boxy_editor.boxy_node = self._boxy_node
        elif node_id:
            # Template node (meshbox, offset, mirror, or parameter)
            self._selected_node_id = node_id
            node = self._template.get_node(node_id)
            if isinstance(node, MeshBoxNode):
                self.edit_panel.custom_type = CustomType.meshbox
            elif isinstance(node, OffsetNode):
                self.edit_panel.custom_type = CustomType.node_offset
            elif isinstance(node, MirrorNode):
                self.edit_panel.custom_type = CustomType.node_mirror
            elif isinstance(node, ParameterNode):
                self.edit_panel.custom_type = CustomType.node_parameter
            else:
                self.edit_panel.custom_type = None
        else:
            self._selected_node_id = None
            self.edit_panel.custom_type = None

    def _on_tree_context_menu(self, position):
        """Show context menu for tree widget."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return

        is_boxy = item.data(0, IS_BOXY_ROLE)
        node_id = item.data(0, NODE_ID_ROLE)

        menu = QMenu(self)

        if is_boxy:
            # Boxy context menu
            add_meshbox_action = menu.addAction("Add Meshbox")
            action = menu.exec_(self.tree_widget.mapToGlobal(position))

            if action == add_meshbox_action:
                self._on_meshbox_button_clicked()
        elif node_id:
            node = self._template.get_node(node_id)
            add_offset_action = None
            add_mirror_action = None

            if isinstance(node, MeshBoxNode):
                # MeshBox context menu - can add offset and mirror
                add_offset_action = menu.addAction("Add Offset")
                add_mirror_action = menu.addAction("Add Mirror")
            delete_action = menu.addAction("Delete")
            action = menu.exec_(self.tree_widget.mapToGlobal(position))

            if action == add_offset_action:
                # Select this meshbox first, then add offset
                self._selected_node_id = node_id
                self._on_offset_button_clicked()
            elif action == add_mirror_action:
                # Select this meshbox first, then add mirror
                self._selected_node_id = node_id
                self._on_mirror_button_clicked()
            elif action == delete_action:
                self._delete_node(node_id)

    def _delete_node(self, node_id: str):
        """Delete a node from the template and Maya scene."""
        node = self._template.get_node(node_id)
        if not node:
            return

        # If deleting a meshbox, also delete its children (offsets, etc.)
        if isinstance(node, MeshBoxNode):
            # Delete Maya geometry if it exists
            if is_using_maya_python() and node.maya_uuid:
                maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
                if maya_node:
                    try:
                        cmds.delete(maya_node)
                    except RuntimeError:
                        pass
                # Remove from preview UUIDs
                if node.maya_uuid in self._preview_uuids:
                    self._preview_uuids.remove(node.maya_uuid)

            # Delete child nodes from template
            for child_id in node.children.copy():
                self._template.remove_node(child_id)

        # If deleting an offset or mirror, remove from parent's children list
        if isinstance(node, (OffsetNode, MirrorNode)) and node.parent_id:
            parent_node = self._template.get_node(node.parent_id)
            if isinstance(parent_node, MeshBoxNode):
                parent_node.remove_child(node_id)
                # Rebuild parent to reflect modifier removal
                if is_using_maya_python():
                    self.rebuild_single_meshbox(parent_node)

        # Remove from template
        self._template.remove_node(node_id)

        # Remove from tree widget (search recursively)
        tree_item = self._find_tree_item_by_node_id(node_id)
        if tree_item:
            parent_item = tree_item.parent()
            if parent_item:
                parent_item.removeChild(tree_item)
            else:
                # Top-level item
                index = self.tree_widget.indexOfTopLevelItem(tree_item)
                if index >= 0:
                    self.tree_widget.takeTopLevelItem(index)

        # If deleting a parameter, update the parameter sliders
        if isinstance(node, ParameterNode):
            self._update_parameter_sliders()
            # Rebuild all meshboxes in case they reference this parameter
            self._rebuild_all_meshboxes()

        # Clear selection
        self._selected_node_id = None
        self.edit_panel.custom_type = None

        self._modified = True
        self.info = f"Deleted: {node.name}"

    def _setup_ui(self):
        """Setup ui."""
        self.document_label.setWordWrap(True)
        self.architype_name_line_edit.textChanged.connect(self._filter_architype_name)
        self.architype_name_line_edit.returnPressed.connect(self._on_architype_name_line_edit_return_pressed)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self._on_tree_widget_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.size_field.values = self.settings.value(self.size_key, self.default_size.values)
        self.size_field.value_changed.connect(self._on_size_field_changed)
        self.pivot_field.selected_anchor = self.default_anchor
        self.pivot_field.anchor_selected.connect(self._on_pivot_changed)
        self._update_ui()

    def _update_ui(self):
        """Update ui."""
        has_boxy = self._boxy_node is not None
        has_name = bool(self.architype_name)
        # Enable Add Meshbox only when we have a name
        self.add_meshbox_button.setEnabled(has_name)

    def _update_parameter_sliders(self):
        """Rebuild the parameter sliders panel based on current parameters."""
        # Clear existing sliders
        for slider in self._parameter_sliders.values():
            slider.setParent(None)
            slider.deleteLater()
        self._parameter_sliders.clear()

        # Clear the parameter panel layout
        self.parameter_panel.clear_widgets()

        # Add sliders for each parameter
        params = self._template.get_all_parameter_nodes()
        for param in params:
            slider = QDoubleSpinBox()
            slider.setRange(param.min_value, param.max_value)
            slider.setSingleStep(param.step)
            slider.setValue(param.value)
            slider.setToolTip(f"${param.name}")

            # Connect value change to update parameter and rebuild
            slider.valueChanged.connect(
                lambda val, p=param: self._on_parameter_slider_changed(p, val)
            )

            self.parameter_panel.add_row(label=f"${param.name}", widget=slider)
            self._parameter_sliders[param.id] = slider

    def _on_parameter_slider_changed(self, param: ParameterNode, value: float):
        """Handle parameter slider value change."""
        param.value = value
        # Rebuild all meshboxes to reflect the parameter change
        self._rebuild_all_meshboxes()

    def _rebuild_all_meshboxes(self):
        """Rebuild all meshbox geometry."""
        if not is_using_maya_python() or not self._validate_boxy_node():
            return

        boxy_data = boxy_utils.get_boxy_data(self._boxy_node)
        boxy_bounds = boxy_utils.get_boxy_bounds(self._boxy_node)

        for node in self._template.get_all_meshbox_nodes():
            # Delete existing geometry
            if node.maya_uuid:
                maya_node = self.get_maya_node_from_uuid(node.maya_uuid)
                if maya_node:
                    try:
                        cmds.delete(maya_node)
                    except RuntimeError:
                        pass
                if node.maya_uuid in self._preview_uuids:
                    self._preview_uuids.remove(node.maya_uuid)
                node.maya_uuid = None

            # Delete mirror geometry
            for mirror_uuid in node.mirror_uuids:
                mirror_node = self.get_maya_node_from_uuid(mirror_uuid)
                if mirror_node:
                    try:
                        cmds.delete(mirror_node)
                    except RuntimeError:
                        pass
                if mirror_uuid in self._preview_uuids:
                    self._preview_uuids.remove(mirror_uuid)
            node.mirror_uuids.clear()

            # Rebuild
            self._build_meshbox_from_node(node, boxy_data, boxy_bounds)

    @property
    def template(self) -> ArchitypeTemplate:
        """The current architype template."""
        return self._template

    @property
    def selected_node_id(self) -> str | None:
        """ID of the currently selected node in the tree widget."""
        return self._selected_node_id

    @property
    def architype_name(self) -> str:
        """Text value of architype_name_line_edit."""
        return self.architype_name_line_edit.text()

    @property
    def boxy_data(self) -> BoxyData | None:
        return self._boxy_data

    @property
    def boxy_node(self) -> str | None:
        return self._boxy_node

    @property
    def boxy_uuid(self) -> str | None:
        return self._boxy_uuid


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
