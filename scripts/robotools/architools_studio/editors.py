"""Editors for Architools."""
from __future__ import annotations

from qtpy.QtWidgets import QLineEdit
from robotools import CustomType
from qtpy.QtWidgets import QCheckBox
from qtpy.QtWidgets import QDoubleSpinBox
from robotools.architools_studio.nodes import MeshBoxNode, MirrorNode, OffsetNode, ParameterNode, SizeValue, SizeMode
from robotools.architools_studio.size_widget import SizeWidget, SizeRowWidget
from widgets.anchor_picker import AnchorPicker
from widgets.float_array_widget import FloatArrayWidget
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget


class Editor(GenericWidget):
    def __init__(self, custom_type: CustomType, parent_widget: GenericWidget):
        super().__init__(title=f"{custom_type.name.capitalize()} Editor")
        self.parent_widget = parent_widget
        self.custom_type = custom_type
        self.add_label(f"{custom_type.name.capitalize()} Editor")


class BoxyEditor(Editor):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.boxy, parent_widget=parent_widget)
        self._updating = False  # Flag to prevent recursive updates

        form: FormWidget = self.add_widget(FormWidget())
        self.boxy_label = form.add_label(label="Boxy node:", default_value="")

        # Size controls
        self.size_widget: FloatArrayWidget = form.add_row(
            label="Size",
            widget=FloatArrayWidget(count=3, default_value=100.0, minimum=1.0, maximum=10000.0, step=1.0)
        )

        # Pivot control
        self.add_label("Pivot")
        self.pivot_picker: AnchorPicker = self.add_widget(AnchorPicker(advanced_mode=True))

        self.boxy_node = None
        self.add_stretch()

        # Connect signals
        self.size_widget.return_pressed.connect(self._on_size_changed)
        self.pivot_picker.anchor_selected.connect(self._on_pivot_changed)

    def refresh(self):
        """Refresh editor from parent's boxy data."""
        if hasattr(self.parent_widget, '_boxy_data') and self.parent_widget._boxy_data:
            self._load_from_boxy_data(self.parent_widget._boxy_data)

    @property
    def boxy_node(self):
        """Boxy node."""
        return self._boxy_node

    @boxy_node.setter
    def boxy_node(self, value):
        self._boxy_node = value
        self.boxy_label.setText(value if value else "None")
        # Load data if boxy node is set
        if value and hasattr(self.parent_widget, '_boxy_data') and self.parent_widget._boxy_data:
            self._load_from_boxy_data(self.parent_widget._boxy_data)

    def _load_from_boxy_data(self, boxy_data):
        """Load UI values from BoxyData."""
        self._updating = True
        try:
            self.size_widget.values = [boxy_data.size.x, boxy_data.size.y, boxy_data.size.z]
            self.pivot_picker.selected_anchor = boxy_data.pivot_anchor
        finally:
            self._updating = False

    def _on_size_changed(self):
        """Handle boxy size change - update Maya node."""
        if self._updating or not self._boxy_node:
            return
        # Delegate to parent widget
        if hasattr(self.parent_widget, 'update_boxy_size'):
            new_size = self.size_widget.values
            self.parent_widget.update_boxy_size(new_size)

    def _on_pivot_changed(self):
        """Handle boxy pivot change - update Maya node."""
        if self._updating or not self._boxy_node:
            return
        # Delegate to parent widget
        if hasattr(self.parent_widget, 'update_boxy_pivot'):
            new_pivot = self.pivot_picker.selected_anchor
            self.parent_widget.update_boxy_pivot(new_pivot)


class MeshboxEditor(Editor):
    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.meshbox, parent_widget=parent_widget)
        self._meshbox_node: MeshBoxNode | None = None
        self._updating = False  # Flag to prevent recursive updates

        # Name field
        form: FormWidget = self.add_widget(FormWidget())
        self.name_edit: QLineEdit = form.add_line_edit(label="Name", placeholder_text="Node name...")

        self.add_label("Pivot (MeshBox origin)")
        self.pivot_picker: AnchorPicker = self.add_widget(AnchorPicker(advanced_mode=True))
        self.add_label("Position (on Boxy)")
        self.position_picker: AnchorPicker = self.add_widget(AnchorPicker(advanced_mode=True))
        self.size_widget: SizeWidget = self.add_widget(SizeWidget())
        self.add_stretch()

        # Connect signals for editing
        self.name_edit.editingFinished.connect(self._on_name_changed)
        self.pivot_picker.anchor_selected.connect(self._on_pivot_changed)
        self.position_picker.anchor_selected.connect(self._on_position_changed)
        self.size_widget.value_changed.connect(self._on_size_changed)
        self.size_widget.mode_changed.connect(self._on_size_mode_changed)

    def refresh(self):
        """Refresh editor from parent's selected node."""
        node_id = self.parent_widget.selected_node_id
        if node_id:
            node = self.parent_widget.template.get_node(node_id)
            if isinstance(node, MeshBoxNode):
                self.meshbox_node = node

    @property
    def meshbox_node(self) -> MeshBoxNode | None:
        return self._meshbox_node

    @meshbox_node.setter
    def meshbox_node(self, value: MeshBoxNode | None):
        self._meshbox_node = value
        self._load_from_node()

    def _load_from_node(self):
        """Load UI values from the current MeshBoxNode."""
        self._updating = True
        try:
            if self._meshbox_node:
                self.name_edit.setText(self._meshbox_node.name)
                self.pivot_picker.selected_anchor = self._meshbox_node.pivot_anchor
                self.position_picker.selected_anchor = self._meshbox_node.position_anchor

                # Update available nodes for linking (exclude current node)
                self._update_available_nodes()

                # Load size modes and values
                self._load_size_row(self.size_widget.width_row, self._meshbox_node.width)
                self._load_size_row(self.size_widget.height_row, self._meshbox_node.height)
                self._load_size_row(self.size_widget.depth_row, self._meshbox_node.depth)
            else:
                self.name_edit.setText("")
        finally:
            self._updating = False

    def _update_available_nodes(self):
        """Update the available nodes for linking in size widget."""
        if not hasattr(self.parent_widget, 'template'):
            return

        # Get all meshbox nodes from template
        nodes = []
        for node in self.parent_widget.template.get_root_nodes():
            if isinstance(node, MeshBoxNode):
                nodes.append((node.id, node.name))

        # Set available nodes, excluding current node
        exclude_id = self._meshbox_node.id if self._meshbox_node else None
        self.size_widget.set_available_nodes(nodes, exclude_id)

    def _load_size_row(self, row, size_value: SizeValue):
        """Load a SizeRowWidget from a SizeValue."""
        if size_value.mode == SizeMode.constant:
            value = size_value.value if isinstance(size_value.value, (int, float)) else 50.0
            row.set_mode("constant", float(value))
        elif size_value.mode in (SizeMode.min, SizeMode.center, SizeMode.max):
            # Lock mode - set lock type and target node
            mode_name = size_value.mode.name  # "min", "center", or "max"
            lock_node_id = size_value.lock_node_id if size_value.lock_node_id else SizeRowWidget.BOXY_ID
            row.set_mode(mode_name, lock_node_id=lock_node_id)
        else:
            # Default to max locked to boxy
            row.set_mode("max")

    def _get_size_display_value(self, size_value: SizeValue) -> float:
        """Get display value for a SizeValue."""
        if size_value.mode == SizeMode.constant:
            if isinstance(size_value.value, (int, float)):
                return float(size_value.value)
            return 50.0  # Default for parameter references
        elif size_value.mode == SizeMode.max:
            return -1.0  # Sentinel for "max" mode (UI will show this differently later)
        return 50.0

    def _on_name_changed(self):
        """Handle node name change - rename Maya node and update UI."""
        if self._updating or not self._meshbox_node:
            return
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self._meshbox_node.name:
            # Rename Maya node and get actual result
            actual_name = self.parent_widget.rename_maya_node(self._meshbox_node, new_name)
            # Update name field with actual name (may differ from requested)
            if actual_name != new_name:
                self._updating = True
                self.name_edit.setText(actual_name)
                self._updating = False
            # Update tree widget item
            self.parent_widget.update_tree_item_name(self._meshbox_node.id, actual_name)
            self.parent_widget.on_template_modified()

    def _on_pivot_changed(self):
        """Handle pivot anchor change - update Maya node pivot."""
        if self._updating or not self._meshbox_node:
            return
        self._meshbox_node.pivot_anchor = self.pivot_picker.selected_anchor
        # Update Maya node pivot
        self.parent_widget.update_maya_meshbox_pivot(self._meshbox_node)
        self.parent_widget.on_template_modified()

    def _on_position_changed(self):
        """Handle position anchor change - reposition Maya node."""
        if self._updating or not self._meshbox_node:
            return
        self._meshbox_node.position_anchor = self.position_picker.selected_anchor
        # Reposition Maya node based on new anchor
        self.parent_widget.update_maya_meshbox_position(self._meshbox_node)
        self.parent_widget.on_template_modified()

    def _on_size_changed(self):
        """Handle size value change (constant mode spinbox)."""
        if self._updating or not self._meshbox_node:
            return
        # Only update if in constant mode
        changed = False
        if self.size_widget.width_row.is_constant_mode:
            self._meshbox_node.width = SizeValue.constant(self.size_widget.width_row.value)
            changed = True
        if self.size_widget.height_row.is_constant_mode:
            self._meshbox_node.height = SizeValue.constant(self.size_widget.height_row.value)
            changed = True
        if self.size_widget.depth_row.is_constant_mode:
            self._meshbox_node.depth = SizeValue.constant(self.size_widget.depth_row.value)
            changed = True

        if changed:
            # Rebuild meshbox with new size
            self.parent_widget.rebuild_single_meshbox(self._meshbox_node)
            self.parent_widget.on_template_modified()

    def _on_size_mode_changed(self):
        """Handle size mode change (Lock/Constant or lock options)."""
        if self._updating or not self._meshbox_node:
            return

        # Get new size values from UI
        new_width = self._get_size_value_from_row(self.size_widget.width_row)
        new_height = self._get_size_value_from_row(self.size_widget.height_row)
        new_depth = self._get_size_value_from_row(self.size_widget.depth_row)

        # Validate no cycles would be created
        if self._would_create_cycle(new_width, new_height, new_depth):
            # Revert to previous state
            self._updating = True
            self._load_size_row(self.size_widget.width_row, self._meshbox_node.width)
            self._load_size_row(self.size_widget.height_row, self._meshbox_node.height)
            self._load_size_row(self.size_widget.depth_row, self._meshbox_node.depth)
            self._updating = False
            if hasattr(self.parent_widget, 'info'):
                self.parent_widget.info = "Cannot lock: would create circular dependency"
            return

        # Update node's SizeValue based on UI mode
        self._meshbox_node.width = new_width
        self._meshbox_node.height = new_height
        self._meshbox_node.depth = new_depth

        # Rebuild the meshbox with new size
        self.parent_widget.rebuild_single_meshbox(self._meshbox_node)
        self.parent_widget.on_template_modified()

    def _would_create_cycle(self, width: SizeValue, height: SizeValue, depth: SizeValue) -> bool:
        """Check if the proposed size values would create a circular dependency.

        A cycle occurs when node A locks to node B, and node B (directly or
        indirectly) locks back to node A.
        """
        if not self._meshbox_node or not hasattr(self.parent_widget, 'template'):
            return False

        # Collect all nodes this node would lock to (excluding boxy)
        locked_ids = set()
        for sv in [width, height, depth]:
            if sv.is_lock_mode and sv.lock_node_id:
                locked_ids.add(sv.lock_node_id)

        if not locked_ids:
            return False

        # Check if any locked node eventually locks back to this node
        visited = set()
        to_check = list(locked_ids)

        while to_check:
            check_id = to_check.pop()
            if check_id in visited:
                continue
            visited.add(check_id)

            # Get the node
            node = self.parent_widget.template.get_node(check_id)
            if not isinstance(node, MeshBoxNode):
                continue

            # Check if this node locks to our node
            for sv in [node.width, node.height, node.depth]:
                if sv.is_lock_mode and sv.lock_node_id:
                    if sv.lock_node_id == self._meshbox_node.id:
                        return True  # Cycle detected!
                    if sv.lock_node_id not in visited:
                        to_check.append(sv.lock_node_id)

        return False

    def _get_size_value_from_row(self, row) -> SizeValue:
        """Convert a SizeRowWidget state to a SizeValue."""
        if row.is_lock_mode:
            lock_type = row.lock_type
            # Get lock target (None for boxy, node ID for meshbox)
            lock_node_id = row.lock_node_id
            if lock_node_id == SizeRowWidget.BOXY_ID:
                lock_node_id = None  # Use None for boxy in SizeValue

            if lock_type == "min":
                return SizeValue.min_size(lock_node_id)
            elif lock_type == "center":
                return SizeValue.center_size(lock_node_id)
            else:  # max
                return SizeValue.max_size(lock_node_id)
        else:
            return SizeValue.constant(row.value)


class OffsetEditor(Editor):
    """Editor for OffsetNode - modifies position of parent MeshBox."""

    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.node_offset, parent_widget=parent_widget)
        self._offset_node: OffsetNode | None = None
        self._updating = False

        form: FormWidget = self.add_widget(FormWidget())
        self.name_label = form.add_label(label="Offset for:", default_value="")

        # Offset controls
        self.offset_widget: FloatArrayWidget = form.add_row(
            label="Offset",
            widget=FloatArrayWidget(
                count=3,
                default_value=0.0,
                minimum=-10000.0,
                maximum=10000.0,
                step=1.0
            )
        )
        self.add_stretch()

        # Connect signals
        self.offset_widget.return_pressed.connect(self._on_offset_changed)

    def refresh(self):
        """Refresh editor from parent's selected node."""
        node_id = self.parent_widget.selected_node_id
        if node_id:
            node = self.parent_widget.template.get_node(node_id)
            if isinstance(node, OffsetNode):
                self.offset_node = node

    @property
    def offset_node(self) -> OffsetNode | None:
        return self._offset_node

    @offset_node.setter
    def offset_node(self, value: OffsetNode | None):
        self._offset_node = value
        self._load_from_node()

    def _load_from_node(self):
        """Load UI values from the current OffsetNode."""
        self._updating = True
        try:
            if self._offset_node:
                # Get parent meshbox name
                parent_node = self.parent_widget.template.get_node(self._offset_node.parent_id)
                parent_name = parent_node.name if parent_node else "Unknown"
                self.name_label.setText(parent_name)
                self.offset_widget.values = [
                    self._offset_node.offset_x,
                    self._offset_node.offset_y,
                    self._offset_node.offset_z
                ]
            else:
                self.name_label.setText("")
                self.offset_widget.values = [0.0, 0.0, 0.0]
        finally:
            self._updating = False

    def _on_offset_changed(self):
        """Handle offset value change."""
        if self._updating or not self._offset_node:
            return

        values = self.offset_widget.values
        self._offset_node.offset_x = values[0]
        self._offset_node.offset_y = values[1]
        self._offset_node.offset_z = values[2]

        # Rebuild parent meshbox
        parent_node = self.parent_widget.template.get_node(self._offset_node.parent_id)
        if isinstance(parent_node, MeshBoxNode):
            self.parent_widget.rebuild_single_meshbox(parent_node)
        self.parent_widget.on_template_modified()


class MirrorEditor(Editor):
    """Editor for MirrorNode - symmetry duplication of parent MeshBox."""

    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.node_mirror, parent_widget=parent_widget)
        self._mirror_node: MirrorNode | None = None
        self._updating = False

        form: FormWidget = self.add_widget(FormWidget())
        self.name_label = form.add_label(label="Mirror for:", default_value="")

        # Mirror axis checkboxes
        self.mirror_x_checkbox: QCheckBox = self.add_widget(QCheckBox("Mirror X (left/right)"))
        self.mirror_z_checkbox: QCheckBox = self.add_widget(QCheckBox("Mirror Z (front/back)"))
        self.add_stretch()

        # Connect signals
        self.mirror_x_checkbox.stateChanged.connect(self._on_mirror_changed)
        self.mirror_z_checkbox.stateChanged.connect(self._on_mirror_changed)

    def refresh(self):
        """Refresh editor from parent's selected node."""
        node_id = self.parent_widget.selected_node_id
        if node_id:
            node = self.parent_widget.template.get_node(node_id)
            if isinstance(node, MirrorNode):
                self.mirror_node = node

    @property
    def mirror_node(self) -> MirrorNode | None:
        return self._mirror_node

    @mirror_node.setter
    def mirror_node(self, value: MirrorNode | None):
        self._mirror_node = value
        self._load_from_node()

    def _load_from_node(self):
        """Load UI values from the current MirrorNode."""
        self._updating = True
        try:
            if self._mirror_node:
                # Get parent meshbox name
                parent_node = self.parent_widget.template.get_node(self._mirror_node.parent_id)
                parent_name = parent_node.name if parent_node else "Unknown"
                self.name_label.setText(parent_name)
                self.mirror_x_checkbox.setChecked(self._mirror_node.mirror_x)
                self.mirror_z_checkbox.setChecked(self._mirror_node.mirror_z)
            else:
                self.name_label.setText("")
                self.mirror_x_checkbox.setChecked(False)
                self.mirror_z_checkbox.setChecked(False)
        finally:
            self._updating = False

    def _on_mirror_changed(self):
        """Handle mirror checkbox change."""
        if self._updating or not self._mirror_node:
            return

        self._mirror_node.mirror_x = self.mirror_x_checkbox.isChecked()
        self._mirror_node.mirror_z = self.mirror_z_checkbox.isChecked()

        # Rebuild parent meshbox
        parent_node = self.parent_widget.template.get_node(self._mirror_node.parent_id)
        if isinstance(parent_node, MeshBoxNode):
            self.parent_widget.rebuild_single_meshbox(parent_node)
        self.parent_widget.on_template_modified()


class ParameterEditor(Editor):
    """Editor for ParameterNode - defines exposed template parameters."""

    def __init__(self, parent_widget: GenericWidget):
        super().__init__(custom_type=CustomType.node_parameter, parent_widget=parent_widget)
        self._parameter_node: ParameterNode | None = None
        self._updating = False

        form: FormWidget = self.add_widget(FormWidget())

        # Parameter name
        self.name_edit: QLineEdit = form.add_line_edit(label="Name", placeholder_text="Parameter name...")

        # Default value
        self.default_spinbox: QDoubleSpinBox = QDoubleSpinBox()
        self.default_spinbox.setRange(-10000.0, 10000.0)
        self.default_spinbox.setValue(10.0)
        form.add_row(label="Default", widget=self.default_spinbox)

        # Min value
        self.min_spinbox: QDoubleSpinBox = QDoubleSpinBox()
        self.min_spinbox.setRange(-10000.0, 10000.0)
        self.min_spinbox.setValue(1.0)
        form.add_row(label="Min", widget=self.min_spinbox)

        # Max value
        self.max_spinbox: QDoubleSpinBox = QDoubleSpinBox()
        self.max_spinbox.setRange(-10000.0, 10000.0)
        self.max_spinbox.setValue(100.0)
        form.add_row(label="Max", widget=self.max_spinbox)

        # Step
        self.step_spinbox: QDoubleSpinBox = QDoubleSpinBox()
        self.step_spinbox.setRange(0.01, 100.0)
        self.step_spinbox.setValue(1.0)
        form.add_row(label="Step", widget=self.step_spinbox)

        self.add_stretch()

        # Connect signals
        self.name_edit.editingFinished.connect(self._on_name_changed)
        self.default_spinbox.valueChanged.connect(self._on_values_changed)
        self.min_spinbox.valueChanged.connect(self._on_values_changed)
        self.max_spinbox.valueChanged.connect(self._on_values_changed)
        self.step_spinbox.valueChanged.connect(self._on_values_changed)

    def refresh(self):
        """Refresh editor from parent's selected node."""
        node_id = self.parent_widget.selected_node_id
        if node_id:
            node = self.parent_widget.template.get_node(node_id)
            if isinstance(node, ParameterNode):
                self.parameter_node = node

    @property
    def parameter_node(self) -> ParameterNode | None:
        return self._parameter_node

    @parameter_node.setter
    def parameter_node(self, value: ParameterNode | None):
        self._parameter_node = value
        self._load_from_node()

    def _load_from_node(self):
        """Load UI values from the current ParameterNode."""
        self._updating = True
        try:
            if self._parameter_node:
                self.name_edit.setText(self._parameter_node.name)
                self.default_spinbox.setValue(self._parameter_node.default_value)
                self.min_spinbox.setValue(self._parameter_node.min_value)
                self.max_spinbox.setValue(self._parameter_node.max_value)
                self.step_spinbox.setValue(self._parameter_node.step)
            else:
                self.name_edit.setText("")
                self.default_spinbox.setValue(10.0)
                self.min_spinbox.setValue(1.0)
                self.max_spinbox.setValue(100.0)
                self.step_spinbox.setValue(1.0)
        finally:
            self._updating = False

    def _on_name_changed(self):
        """Handle parameter name change."""
        if self._updating or not self._parameter_node:
            return
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self._parameter_node.name:
            self._parameter_node.name = new_name
            # Update tree widget
            self.parent_widget.update_tree_item_name(self._parameter_node.id, new_name)
            self.parent_widget.on_template_modified()

    def _on_values_changed(self):
        """Handle parameter value changes."""
        if self._updating or not self._parameter_node:
            return
        self._parameter_node.default_value = self.default_spinbox.value()
        self._parameter_node.min_value = self.min_spinbox.value()
        self._parameter_node.max_value = self.max_spinbox.value()
        self._parameter_node.step = self.step_spinbox.value()
        # Reset current value to default when default changes
        self._parameter_node.reset()
        self.parent_widget.on_template_modified()
