"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
# UI for Boxy.
import contextlib
import logging

import robotools
from qtpy.QtCore import Qt, QSettings
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QCheckBox, QColorDialog, QDoubleSpinBox, QSizePolicy

from core import color_classes, DEVELOPER, logging_utils
from core.color_classes import ColorRGB
from core.core_enums import ComponentType, CreationMode, Side, SurfaceDirection
from robotools import CustomType
from core.core_paths import image_path
from robotools.anchor import Anchor
from robotools.boxy import boxy_utils, VERSIONS, TOOL_NAME
from robotools.boxy.boxy_settings_dialog import BoxySettingsDialog, get_advanced_pivot_mode
from widgets.anchor_picker import AnchorPicker
from widgets.button_bar import ButtonBar
from widgets.clickable_label import ClickableLabel
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.image_label import ImageLabel

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import attribute_utils, maya_widget_utils, node_utils
    from maya_tools.geometry import face_finder
    from maya_tools.geometry.component_utils import FaceComponent, components_from_selection
    from robotools.architools import arch_utils

# All architypes that can be converted
ARCHITYPES = (CustomType.window, CustomType.door, CustomType.staircase)
LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)



class BoxyTool(GenericWidget):
    """Boxy UI Class."""
    button_size = 32
    color_key = "color"
    inherit_rotation_key = "inherit_rotation"
    inherit_scale_key = "inherit_scale"
    pivot_anchor_key = "pivot_anchor"
    size_key = "size"

    def __init__(self):
        super().__init__(title=VERSIONS.title, margin=2, spacing=2)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        header: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        logo = header.add_widget(ImageLabel(path=image_path("boxy_icon.png")))
        logo.setFixedSize(self.button_size, self.button_size)
        header_label: QLabel = header.add_label("boxy tool", side=Side.left)
        header_label.setStyleSheet("font-size: 24pt; font-family: BM Dohyeon, Arial;")
        header.add_stretch()
        left_alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        button_bar: ButtonBar = self.add_widget(ButtonBar(button_size=self.button_size))
        button_bar.add_icon_button(icon_path=image_path("boxy.png"), tool_tip="Create Boxy", clicked=self.create_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("polycube.png"), tool_tip="Create Polycube", clicked=self.polycube_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_concave.png"), tool_tip="Concave boxy from face", clicked=self.concave_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_convex.png"), tool_tip="Convex boxy from face", clicked=self.convex_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("settings.png"), tool_tip="Settings", clicked=self.settings_button_clicked)
        button_bar.add_stretch()
        button_bar.add_icon_button(icon_path=image_path("dr_steve_brule.png"), tool_tip="Help", clicked=self.help_button_clicked)
        grid: GridWidget = self.add_group_box(GridWidget(title="Boxy Parameters", spacing=8))
        grid.add_label(text="Pivot Position", row=0, column=0, alignment=left_alignment)
        self.anchor_picker: AnchorPicker = grid.add_widget(
            widget=AnchorPicker(advanced_mode=get_advanced_pivot_mode()),
            row=0, column=1
        )
        self.anchor_picker.setFixedHeight(90)
        grid.add_label(text="Wireframe Color", row=1, column=0, alignment=left_alignment)
        self.color_picker: ClickableLabel = grid.add_widget(widget=ClickableLabel(""), row=1, column=1)
        grid.add_label(text="Default Size", row=2, column=0, alignment=left_alignment)
        self.size_field: QDoubleSpinBox = grid.add_widget(widget=QDoubleSpinBox(), row=2, column=1)
        grid.add_label(text="Inherit Rotation", row=3, column=0, alignment=left_alignment)
        self.rotation_check_box: QCheckBox = grid.add_widget(widget=QCheckBox(), row=3, column=1)
        grid.add_label(text="Inherit Scale", row=4, column=0, alignment=left_alignment)
        self.scale_check_box: QCheckBox = grid.add_widget(widget=QCheckBox(), row=4, column=1)
        self.add_stretch()
        self.info_label = self.add_label(text="Ready...", side=Side.left)
        default_color = self.settings.value(self.color_key, color_classes.DEEP_GREEN.values)
        self.wireframe_color = ColorRGB(*default_color)
        self._setup_ui()

    def _create_boxy_from_face(self, surface_direction: SurfaceDirection):
        """Create a Boxy from a selected face and its opposite face."""
        components = components_from_selection()

        # Validate single face selection
        if len(components) != 1 or not isinstance(components[0], FaceComponent):
            self.info = "Select a single face"
            return

        face = components[0]

        # Find opposite face
        opposite = face_finder.get_opposite_face(
            component=face,
            surface_direction=surface_direction,
            select=False
        )

        if opposite is None:
            self.info = "No matching face found"
            return

        # Select both faces and create Boxy
        cmds.select([face.name, opposite.name], replace=True)
        cmds.hilite(face.transform)
        self.create_button_clicked()

    def _setup_ui(self):
        """Set up ui."""
        self.color_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.rotation_check_box.setChecked(self.settings.value(self.inherit_rotation_key, True))
        self.rotation_check_box.stateChanged.connect(self.rotation_check_box_state_changed)
        self.scale_check_box.setChecked(self.settings.value(self.inherit_scale_key, True))
        self.scale_check_box.stateChanged.connect(self.scale_check_box_state_changed)
        self.color_picker.clicked.connect(self.color_picker_clicked)
        # Restore saved anchor selection
        saved_anchor_name = self.settings.value(self.pivot_anchor_key, "c")
        try:
            saved_anchor = Anchor[saved_anchor_name]
            self.anchor_picker.selected_anchor = saved_anchor
        except KeyError:
            self.anchor_picker.selected_anchor = Anchor.c
        self.anchor_picker.anchor_selected.connect(self.anchor_picker_selection_changed)
        self.size_field.setValue(self.settings.value(self.size_key, 10.0))
        self.size_field.setRange(0.1, 100000.0)
        self.size_field.setDecimals(1)
        self.size_field.setSingleStep(0.1)
        self.size_field.valueChanged.connect(self.size_field_value_changed)

    @property
    def default_size(self):
        """Default size."""
        return self.size_field.value()

    @property
    def info(self) -> str:
        """Text value of the info label."""
        return self.info_label.text()

    @info.setter
    def info(self, text: str) -> None:
        self.info_label.setText(text)

    @property
    def inherit_rotation(self) -> bool:
        """Value of the rotation check box."""
        return self.rotation_check_box.isChecked()

    @property
    def inherit_scale(self) -> bool:
        """Value of the rotation check box."""
        return self.scale_check_box.isChecked()

    @property
    def pivot(self) -> Anchor:
        return self.anchor_picker.selected_anchor

    @property
    def wireframe_color(self) -> ColorRGB:
        """Color for the boxy wireframe."""
        return self._wireframe_color

    @wireframe_color.setter
    def wireframe_color(self, value: ColorRGB):
        self._wireframe_color = value
        self.color_picker.setStyleSheet(f"background-color: {value.css};")
        self.settings.setValue(self.color_key, value.values)

    def color_picker_clicked(self):
        """Event for color-picker."""
        default = QColor()
        default.setRgb(*self.wireframe_color.values)
        color = QColorDialog.getColor(default)
        if color.isValid():
            self.wireframe_color = ColorRGB(color.red(), color.green(), color.blue())

    def concave_face_button_clicked(self):
        """Event for concave face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.concave)

    def convex_face_button_clicked(self):
        """Event for convex face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.convex)

    def create_button_clicked(self):
        """Event for create button.

        Context-sensitive boxy conversion:
        - Nothing selected: create default size boxy at origin
        - Boxy nodes: rebuild with current settings
        - Architype nodes (window, door, staircase): convert to boxy
        - Polycube nodes: convert to boxy
        - Other selection (vertices, faces, etc.): create new boxy from bounds
        """
        from core.point_classes import Point3
        from robotools.boxy.boxy_data import BoxyData

        # Capture selected transforms before any conversions
        selected_transforms = list(node_utils.get_selected_transforms(full_path=True))
        original_selection = cmds.ls(selection=True)
        boxy_items = []
        exceptions = []

        # If nothing selected, create default boxy at origin
        if not selected_transforms:
            size = self.default_size
            boxy_data = BoxyData(
                size=Point3(size, size, size),
                translation=Point3(0, 0, 0),
                rotation=Point3(0, 0, 0),
                pivot_anchor=self.pivot,
                color=self.wireframe_color
            )
            result = boxy_utils.build(boxy_data=boxy_data)
            self.info = f"Boxy object created: {result}"
            cmds.select(result)
            return

        has_convertible_nodes = False

        # Check for convertible nodes first
        for node in selected_transforms:
            if robotools.is_boxy(node):
                has_convertible_nodes = True
            elif any(robotools.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                has_convertible_nodes = True
            elif boxy_utils.is_polycube(node):
                has_convertible_nodes = True

        if has_convertible_nodes:
            # Process each node individually for conversion using full paths
            for node in selected_transforms:
                if not cmds.objExists(node):
                    continue
                if robotools.is_boxy(node):
                    # Rebuild boxy with current settings
                    cmds.select(node)
                    rebuilt_nodes, rebuild_exceptions = boxy_utils.Boxy(color=self.wireframe_color).create(
                        pivot=self.pivot, inherit_rotations=self.inherit_rotation,
                        inherit_scale=self.inherit_scale)
                    boxy_items.extend(rebuilt_nodes)
                    exceptions.extend(rebuild_exceptions)
                elif any(robotools.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                    # Convert architype to boxy
                    result = arch_utils.convert_node_to_boxy(node=node, delete=True)
                    if result:
                        boxy_items.append(result)
                elif boxy_utils.is_polycube(node):
                    # Convert polycube to boxy
                    result = boxy_utils.convert_polycube_to_boxy(polycube=node, color=self.wireframe_color, pivot=self.pivot, inherit_scale=self.inherit_scale)
                    if result:
                        boxy_items.append(result)
        else:
            # No convertible nodes - use original behavior to create boxy from selection
            creator = boxy_utils.Boxy(color=self.wireframe_color)
            boxy_items, exceptions = creator.create(
                pivot=self.pivot, inherit_rotations=self.inherit_rotation,
                inherit_scale=self.inherit_scale, default_size=self.default_size)

        # Report results
        if len(exceptions) > 0:
            exception_string = ", ".join(ex.message for ex in exceptions)
            self.info = f"Issues found: {exception_string}"
        elif len(boxy_items) == 0:
            self.info = "No boxy objects created."
            cmds.select(original_selection)
        else:
            if len(boxy_items) == 1:
                self.info = f"Boxy object created: {boxy_items[0]}"
            else:
                self.info = f"Boxy objects created: {', '.join(boxy_items)}"
            cmds.select(boxy_items)
            node_utils.set_component_mode(ComponentType.object)
            cmds.hilite(boxy_items, unHilite=True)

    def help_button_clicked(self):
        """Event for help button."""
        from robotools.boxy.boxy_help import BoxyHelp
        help_widgets = maya_widget_utils.get_widget_instances(tool_class="BoxyHelp")
        help_widget = help_widgets[-1] if help_widgets else BoxyHelp(parent_widget=self)
        help_widget.show()

    def anchor_picker_selection_changed(self, anchor: Anchor):
        """Event for anchor picker selection."""
        self.settings.setValue(self.pivot_anchor_key, anchor.name)

    def settings_button_clicked(self):
        """Event for settings button."""
        dialog = BoxySettingsDialog(parent=self)
        if dialog.exec():
            # Update anchor picker mode based on settings
            self.anchor_picker.advanced_mode = get_advanced_pivot_mode()

    def polycube_button_clicked(self):
        """Event for Create Polycube button.

        Context-sensitive polycube conversion:
        - Nothing selected: create default size polycube at origin with selected pivot
        - Boxy nodes: convert to polycube
        - Architype nodes: convert to boxy first, then to polycube
        - Polycube nodes: recalculate (reset transforms, use selected pivot)
        - Other: no action (only handles boxy-related nodes)
        """
        from core.point_classes import Point3

        # Capture selected transforms before any conversions
        selected_transforms = list(node_utils.get_selected_transforms(full_path=True))
        polycube_items = []

        # If nothing selected, create default polycube at origin
        if not selected_transforms:
            size = self.default_size
            polycube = boxy_utils.create_polycube(
                pivot=self.pivot,
                size=Point3(size, size, size),
                creation_mode=CreationMode.pivot_origin,
                construction_history=False,
            )
            self.info = f"Polycube created: {polycube}"
            cmds.select(polycube)
            return

        # Categorize all nodes BEFORE any conversions (to avoid shared history issues)
        boxy_nodes = []
        architype_nodes = []
        polycube_nodes = []
        for node in selected_transforms:
            if not cmds.objExists(node):
                continue
            if robotools.is_boxy(node):
                boxy_nodes.append(node)
            elif any(robotools.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                architype_nodes.append(node)
            elif boxy_utils.is_polycube(node):
                polycube_nodes.append(node)
            elif boxy_utils.is_simple_cuboid(node):
                # Cuboid without polycube attributes - still convertible
                polycube_nodes.append(node)

        # Process boxy nodes
        for node in boxy_nodes:
            if not cmds.objExists(node):
                continue
            result = boxy_utils.convert_boxy_to_polycube(node=node, pivot=self.pivot, inherit_scale=self.inherit_scale)
            if result and not isinstance(result, boxy_utils.BoxyException):
                polycube_items.append(result)

        # Process architype nodes
        for node in architype_nodes:
            if not cmds.objExists(node):
                continue
            boxy_node = arch_utils.convert_node_to_boxy(node=node, delete=True)
            if boxy_node:
                result = boxy_utils.convert_boxy_to_polycube(node=boxy_node, pivot=self.pivot, inherit_scale=self.inherit_scale)
                if result and not isinstance(result, boxy_utils.BoxyException):
                    polycube_items.append(result)

        # Process polycube nodes - uses pivot from UI anchor picker
        for node in polycube_nodes:
            if not cmds.objExists(node):
                continue
            boxy_node = boxy_utils.convert_polycube_to_boxy(
                polycube=node, color=self.wireframe_color, pivot=self.pivot, inherit_scale=self.inherit_scale)
            if boxy_node:
                result = boxy_utils.convert_boxy_to_polycube(node=boxy_node, pivot=self.pivot, inherit_scale=self.inherit_scale)
                if result and not isinstance(result, boxy_utils.BoxyException):
                    polycube_items.append(result)

        # Report results and select
        if polycube_items:
            if len(polycube_items) == 1:
                self.info = f"Polycube created: {polycube_items[0]}"
            else:
                self.info = f"Polycubes created: {', '.join(polycube_items)}"
            cmds.select(polycube_items)
            node_utils.set_component_mode(ComponentType.object)
        else:
            self.info = "No polycubes created."

    def rotation_check_box_state_changed(self):
        """Event for scale checkbox state change."""
        self.settings.setValue(self.inherit_rotation_key, self.inherit_rotation)

    def scale_check_box_state_changed(self):
        """Event for scale checkbox state change."""
        self.settings.setValue(self.inherit_scale_key, self.inherit_scale)

    def size_field_value_changed(self, arg):
        """Event for size field."""
        self.settings.setValue(self.size_key, arg)


def launch():
    """Launch Boxy Tool."""
    maya_widget_utils.launch_tool(
        tool_module="robotools.boxy.boxy_tool",
        tool_class="BoxyTool",
        use_workspace_control=True,
        ui_script="from robotools.boxy import boxy_tool; boxy_tool.BoxyTool().restore()",
    )

if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    window = BoxyTool()
    window.show()
    app.exec()
