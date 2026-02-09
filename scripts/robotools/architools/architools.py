# Staircase Creator Tool
from __future__ import annotations

import contextlib

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDoubleSpinBox, QTabWidget

from core import DEVELOPER
from core.core_enums import ComponentType, CreationMode, Side, SurfaceDirection
from core.core_paths import image_path
from maya_tools import maya_widget_utils
from robotools import CustomType
from robotools.architools import TOOL_NAME, VERSIONS, ARCHITOOLS_COLOR, arch_utils
from robotools.architools.widgets.door_widget import DoorWidget
from robotools.architools.widgets.staircase_widget import StaircaseWidget
from robotools.architools.widgets.window_widget import WindowWidget
from widgets.button_bar import ButtonBar
from widgets.form_widget import FormWidget
from widgets.generic_widget import GenericWidget
from widgets.image_label import ImageLabel

# All architypes that can be converted
ARCHITYPES = (CustomType.window, CustomType.door, CustomType.staircase)

with contextlib.suppress(ImportError):
    from maya import cmds
    from maya_tools import node_utils
    from maya_tools.geometry import face_finder
    from maya_tools.geometry.component_utils import FaceComponent, components_from_selection
    from robotools.boxy import boxy_utils


class Architools(GenericWidget):
    auto_texture_check_box_state = "auto_texture_check_box_state"
    default_cube_size_key = "default_cube_size"
    skirt_thickness_key = "skirt_thickness"
    tab_index_key = "tab_index"
    xray_mode_key = "xray_mode"

    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self.logo = self.add_widget(ImageLabel(image_path("architools_logo.png")))
        button_bar: ButtonBar = self.add_widget(ButtonBar())
        button_bar.add_icon_button(
            icon_path=image_path("boxy_architools.png"), tool_tip="Create Boxy", clicked=self.boxy_clicked)
        button_bar.add_icon_button(icon_path=image_path("polycube.png"), tool_tip="Create Polycube", clicked=self.polycube_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_concave_architools.png"), tool_tip="Concave boxy from face",
                                   clicked=self.concave_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("boxy_face_convex_architools.png"), tool_tip="Convex boxy from face",
                                   clicked=self.convex_face_button_clicked)
        button_bar.add_icon_button(icon_path=image_path("rotate_90.png"), tool_tip="Change Orientation 90°", clicked=self.rotate_button_clicked)
        button_bar.add_stretch()
        button_bar.add_icon_button(icon_path=image_path("help.png"), tool_tip="Help", clicked=self.help_button_clicked)
        general_form: FormWidget = self.add_group_box(FormWidget(title="General Attributes"))
        self.skirt_thickness_input: QDoubleSpinBox = general_form.add_float_field(
            label="Skirt Thickness", default_value=2.0, minimum=0.5, maximum=5.0, step=0.1)
        self.auto_texture_check_box = general_form.add_check_box(
            label="Auto-texture", tool_tip="Apply checker texture")
        self.default_cube_size_input:  QDoubleSpinBox = general_form.add_float_field(
            label="Default Cube Size", default_value=50.0, minimum=1.0, maximum=1000.0, step=1.0)
        self.xray_mode_check_box = general_form.add_check_box(label="Ghost Cube Mode", checked=False, tool_tip="Set the xray mode on cubes")
        self.tab_widget: QTabWidget = self.add_widget(QTabWidget())
        self.tab_widget.addTab(DoorWidget(parent=self), DoorWidget().windowTitle())
        self.tab_widget.addTab(WindowWidget(parent=self), WindowWidget().windowTitle())
        self.tab_widget.addTab(StaircaseWidget(parent=self), StaircaseWidget().windowTitle())
        self.info_label = self.add_label("Ready...", side=Side.left)
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
        self.boxy_clicked()

    def _setup_ui(self):
        auto_texture_check_box_state = self.settings.value(self.auto_texture_check_box_state, True)
        self.auto_texture_check_box.setChecked(auto_texture_check_box_state)
        self.auto_texture_check_box.stateChanged.connect(self.auto_texture_check_box_state_changed)
        self.default_cube_size_input.setValue(self.settings.value(self.default_cube_size_key, 50.0))
        self.default_cube_size_input.valueChanged.connect(
            lambda: self.settings.setValue(self.default_cube_size_key, self.default_cube_size))
        self.skirt_thickness_input.setValue(self.settings.value(self.skirt_thickness_key, 2.0))
        self.skirt_thickness_input.valueChanged.connect(
            lambda: self.settings.setValue(self.skirt_thickness_key, self.skirt_thickness))
        self.xray_mode_check_box.setChecked(self.settings.value(self.xray_mode_key, False))
        self.xray_mode_check_box.stateChanged.connect(
            lambda: self.settings.setValue(self.xray_mode_key, self.xray_mode))
        self.tab_widget.setCurrentIndex(self.settings.value(self.tab_index_key, 0))
        self.tab_widget.currentChanged.connect(lambda: self.settings.setValue(
            self.tab_index_key, self.tab_widget.currentIndex()))
        self.logo.setFixedHeight(80)

    @property
    def info(self) -> str:
        return self.info_label.text()

    @property
    def auto_texture(self) -> bool:
        return self.auto_texture_check_box.isChecked()

    @info.setter
    def info(self, value: str):
        self.info_label.setText(value)

    @property
    def default_cube_size(self) -> float:
        return self.default_cube_size_input.value()

    @property
    def skirt_thickness(self) -> float:
        """Value of the skirt_thickness_input."""
        return self.skirt_thickness_input.value()

    @property
    def xray_mode(self) -> bool:
        """Value of the xray_mode_check box."""
        return self.xray_mode_check_box.isChecked()

    def auto_texture_check_box_state_changed(self):
        """Event for auto_texture_check_box."""
        self.settings.setValue(self.auto_texture_check_box_state, self.auto_texture)

    def boxy_clicked(self):
        """Event for main boxy button.

        Context-sensitive boxy conversion:
        - Nothing selected: create default size boxy at origin
        - Boxy nodes: rebuild as ARCHITOOLS_COLOR bottom pivot boxy
        - Architype nodes (window, door, staircase): convert to boxy
        - Polycube nodes: convert to boxy
        - Other selection (vertices, faces, etc.): create new boxy from bounds
        """
        # Capture selected transforms before any conversions
        selected_transforms = list(node_utils.get_selected_transforms(full_path=True))
        original_selection = cmds.ls(selection=True)
        boxy_items = []
        exceptions = []

        # If nothing selected, create default boxy at origin
        if not selected_transforms:
            from core.point_classes import Point3
            from robotools.boxy.boxy_data import BoxyData
            size = self.default_cube_size
            boxy_data = BoxyData(
                size=Point3(size, size, size),
                translation=Point3(0, 0, 0),
                rotation=Point3(0, 0, 0),
                pivot_side=Side.bottom,
                color=ARCHITOOLS_COLOR
            )
            result = boxy_utils.build(boxy_data=boxy_data)
            self.info = f"Boxy object created: {result}"
            cmds.select(result)
            return

        has_convertible_nodes = False

        # Check for convertible nodes first
        for node in selected_transforms:
            if node_utils.is_boxy(node):
                has_convertible_nodes = True
            elif any(node_utils.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                has_convertible_nodes = True
            elif boxy_utils.is_polycube(node):
                has_convertible_nodes = True

        if has_convertible_nodes:
            # Process each node individually for conversion
            for node in selected_transforms:
                # Skip if node no longer exists (may have been affected by previous conversion)
                if not cmds.objExists(node):
                    continue
                if node_utils.is_boxy(node):
                    # Rebuild boxy with ARCHITOOLS_COLOR and bottom pivot
                    cmds.select(node)
                    rebuilt_nodes, rebuild_exceptions = boxy_utils.Boxy(color=ARCHITOOLS_COLOR).create(
                        pivot=Side.bottom)
                    boxy_items.extend(rebuilt_nodes)
                    exceptions.extend(rebuild_exceptions)
                elif any(node_utils.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                    # Convert architype to boxy
                    result = arch_utils.convert_node_to_boxy(node=node, delete=True)
                    if result:
                        boxy_items.append(result)
                elif boxy_utils.is_polycube(node):
                    # Convert polycube to boxy (Architools always uses bottom pivot)
                    result = boxy_utils.convert_polycube_to_boxy(polycube=node, color=ARCHITOOLS_COLOR, pivot=Side.bottom)
                    if result:
                        boxy_items.append(result)
        else:
            # No convertible nodes - use original behavior to create boxy from selection
            creator: boxy_utils.Boxy = boxy_utils.Boxy(color=ARCHITOOLS_COLOR)
            boxy_items, exceptions = creator.create(
                pivot=Side.bottom, default_size=self.default_cube_size)

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

    def polycube_button_clicked(self):
        """Event for Create Polycube button.

        Context-sensitive polycube conversion:
        - Nothing selected: create default size polycube at origin with bottom pivot
        - Boxy nodes: convert to polycube
        - Architype nodes: convert to polycube (same size as if converted to boxy first)
        - Polycube nodes: recalculate (reset transforms, pivot to bottom center)
        - Other: no action (only handles architools-related nodes)
        """
        from core.point_classes import Point3

        # Capture selected transforms before any conversions
        selected_transforms = list(node_utils.get_selected_transforms(full_path=True))
        polycube_items = []

        # If nothing selected, create default polycube at origin
        if not selected_transforms:
            size = self.default_cube_size
            polycube = boxy_utils.create_polycube(
                pivot_side=Side.bottom,
                size=Point3(size, size, size),
                creation_mode=CreationMode.pivot_origin,
                construction_history=False,
            )
            # TODO: xray mode disabled due to Maya viewport refresh bug
            # if self.xray_mode:
            #     geometry_utils.toggle_xray()
            self.info = f"Polycube created: {polycube}"
            cmds.select(polycube)
            return

        # Process each selected node
        for node in selected_transforms:
            # Skip if node no longer exists (may have been affected by previous conversion)
            if not cmds.objExists(node):
                continue
            if node_utils.is_boxy(node):
                # Convert boxy to polycube (Architools always uses bottom pivot)
                result = boxy_utils.convert_boxy_to_polycube(node=node, pivot=Side.bottom)
                if result and not isinstance(result, boxy_utils.BoxyException):
                    polycube_items.append(result)
            elif any(node_utils.is_custom_type(node=node, custom_type=ct) for ct in ARCHITYPES):
                # Convert architype to boxy first, then to polycube
                boxy_node = arch_utils.convert_node_to_boxy(node=node, delete=True)
                if boxy_node:
                    result = boxy_utils.convert_boxy_to_polycube(node=boxy_node, pivot=Side.bottom)
                    if result and not isinstance(result, boxy_utils.BoxyException):
                        polycube_items.append(result)
            elif boxy_utils.is_polycube(node):
                # Recalculate polycube: convert to boxy then back to polycube
                # This resets transforms and puts pivot to bottom center
                boxy_node = boxy_utils.convert_polycube_to_boxy(polycube=node, color=ARCHITOOLS_COLOR, pivot=Side.bottom)
                if boxy_node:
                    result = boxy_utils.convert_boxy_to_polycube(node=boxy_node, pivot=Side.bottom)
                    if result and not isinstance(result, boxy_utils.BoxyException):
                        polycube_items.append(result)
            # Other node types: no action

        # Report results and select
        if polycube_items:
            if len(polycube_items) == 1:
                self.info = f"Polycube created: {polycube_items[0]}"
            else:
                self.info = f"Polycubes created: {', '.join(polycube_items)}"
            cmds.select(polycube_items)
            # TODO: xray mode disabled due to Maya viewport refresh bug
            # if self.xray_mode:
            #     geometry_utils.toggle_xray()
        else:
            self.info = "No polycubes created."

    def concave_face_button_clicked(self):
        """Event for concave face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.concave)

    def convex_face_button_clicked(self):
        """Event for convex face button."""
        self._create_boxy_from_face(surface_direction=SurfaceDirection.convex)

    def help_button_clicked(self):
        """Event for help button."""
        from robotools.architools.architools_help import ArchitoolsHelp
        help_widgets = maya_widget_utils.get_widget_instances(tool_class="ArchitoolsHelp")
        help_widget = help_widgets[-1] if help_widgets else ArchitoolsHelp(parent_widget=self)
        help_widget.show()
        self.info = "Help displayed"

    def rotate_button_clicked(self):
        """Event for rotate button.

        Rotates orientation (not regular rotation) by -90 degrees on Y axis.
        - Architype nodes: convert to boxy, rotate orientation, convert back to same architype
        - Boxy nodes: rotate orientation
        - Polycube nodes: convert to boxy, rotate orientation, convert back to polycube
        - Other nodes: no action
        """
        from core.core_enums import Axis

        rotated_items = []
        selected_transforms = node_utils.get_selected_transforms(full_path=True)

        if not selected_transforms:
            self.info = "No valid item selected for rotation"
            return

        for node in selected_transforms:
            # Check for architype nodes
            detected_type = None
            for ct in ARCHITYPES:
                if node_utils.is_custom_type(node=node, custom_type=ct):
                    detected_type = ct
                    break

            if detected_type:
                # Architype: convert to boxy, rotate, convert back to same architype
                temp_boxy = arch_utils.convert_node_to_boxy(node=node, delete=True)
                if temp_boxy:
                    rotated_boxy = boxy_utils.edit_boxy_orientation(node=temp_boxy, rotation=-90, axis=Axis.y)
                    if rotated_boxy:
                        # Get the appropriate widget to generate the architype
                        cmds.select(rotated_boxy)
                        widget_index = {CustomType.door: 0, CustomType.window: 1, CustomType.staircase: 2}[detected_type]
                        widget = self.tab_widget.widget(widget_index)
                        result = widget.generate_architype()
                        if result:
                            rotated_items.append(result)
            elif node_utils.is_boxy(node):
                # Boxy: just rotate orientation
                result = boxy_utils.edit_boxy_orientation(node=node, rotation=-90, axis=Axis.y)
                if result:
                    rotated_items.append(result)
            elif boxy_utils.is_polycube(node):
                # Polycube: convert to boxy, rotate, convert back to polycube
                temp_boxy = boxy_utils.convert_polycube_to_boxy(polycube=node, color=ARCHITOOLS_COLOR, pivot=Side.bottom)
                if temp_boxy:
                    rotated_boxy = boxy_utils.edit_boxy_orientation(node=temp_boxy, rotation=-90, axis=Axis.y)
                    if rotated_boxy:
                        result = boxy_utils.convert_boxy_to_polycube(node=rotated_boxy, pivot=Side.bottom)
                        if result and not isinstance(result, boxy_utils.BoxyException):
                            rotated_items.append(result)

        if rotated_items:
            if len(rotated_items) == 1:
                self.info = f"Rotated: {rotated_items[0]}"
            else:
                self.info = f"Rotated {len(rotated_items)} items"
            cmds.select(rotated_items)
        else:
            self.info = "No valid item selected for rotation"


def launch():
    """Launch Boxy Tool."""
    maya_widget_utils.launch_tool(
        tool_module="robotools.architools.architools",
        tool_class="Architools",
        use_workspace_control=True,
        ui_script="from robotools.architools import architools; architools.Architools().restore()",
    )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = Architools()
    tool.show()
    app.exec_()
