from functools import partial
from maya import cmds
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox
from PySide6.QtCore import QSettings

# DEBUG BLOCK START
from importlib import reload
from maya_tools import node_utils; reload(node_utils)
from maya_tools import helpers; reload(helpers)
from maya_tools import rigging_utils; reload(rigging_utils)
# DEBUG BLOCK END

from core import DEVELOPER
from core.core_enums import Axis
from core.point_classes import POINT3_ORIGIN
from maya_tools.character_utils import mirror_limbs
from maya_tools.helpers import get_midpoint_from_transform, create_locator, create_pivot_locators, auto_parent_locators
from maya_tools.node_utils import ComponentType, set_component_mode, pivot_to_center, match_pivot_to_last, \
    get_locators
from maya_tools.rigging_utils import create_joints_from_locator_hierarchy, create_locator_hierarchy_from_joints, \
    bind_skin, orient_joints
from maya_tools.undo_utils import UndoStack
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.group_box import GroupBox
from widgets.radio_button_widget import RadioButtonWidget


class RigBuilder(GridWidget):
    TITLE: str = 'Rig Builder'
    MIRROR_KEY: str = 'mirror'
    SIZE_KEY: str = 'size'

    def __init__(self):
        super(RigBuilder, self).__init__(title=self.TITLE)
        self.settings: QSettings = QSettings(DEVELOPER, self.TITLE)
        self.axis_selector: RadioButtonWidget = self.add_widget(
            RadioButtonWidget(title='Mirror Axis', button_text_list=['X', 'Y', 'Z']), row=0, column=0, col_span=2)
        self.add_label('Size', row=1, column=0)
        self.size_input: QDoubleSpinBox = self.add_widget(QDoubleSpinBox(), row=1, column=1)
        self.mirror_check_box: QCheckBox = self.add_widget(QCheckBox('Mirror Joints'), row=2, column=0, col_span=2)
        self.add_button('Create Joints From Locators', event=self.create_joints_from_locators_clicked, row=3, column=0, col_span=2,
                        tool_tip='Build the joints from the locator hierarchy.')
        self.add_button('Create Locators From Joints', event=self.create_locators_from_joints_clicked, row=4, column=0, col_span=2,
                        tool_tip='Build the locator hierarchy from selected joints.')
        self.add_button('Create Locator At Selection Center', row=5, column=0, col_span=2,
                        event=self.create_locator_at_selection_center_clicked,
                        tool_tip='Create locator at the center of selected components.')
        self.add_button('Create Locators From Pivots', row=6, column=0, col_span=2,
                        event=self.create_pivot_locators_clicked,
                        tool_tip='Create locators at selected pivot positions.')
        self.add_button('Auto-Parent Locators', row=7, column=0, col_span=2, event=auto_parent_locators,
                        tool_tip='Create a hierarchy from selected locators based on selection order.')
        self.add_button('Delete locators', row=8, column=0, col_span=2, event=partial(cmds.delete, get_locators()),
                        tool_tip='Purge all locators.')
        self.setup_ui()

    def setup_ui(self):
        self.size_input.setValue(self.settings.value(self.SIZE_KEY, defaultValue=1.))
        self.size_input.setMinimum(.1)
        self.size_input.setMaximum(10.)
        self.size_input.valueChanged.connect(self.size_changed)
        self.mirror_check_box.setChecked(self.settings.value(self.MIRROR_KEY, defaultValue=False))
        self.mirror_check_box.stateChanged.connect(self.mirror_check_box_changed)

    @property
    def current_axis(self) -> Axis:
        return Axis.get_by_key(self.axis_selector.current_text.lower())

    @property
    def current_size(self) -> float:
        return self.size_input.value()

    @property
    def mirror_joints(self) -> bool:
        return self.mirror_check_box.isChecked()

    def size_changed(self):
        """
        Event for size input
        """
        self.settings.setValue(self.SIZE_KEY, self.current_size)

    def mirror_check_box_changed(self):
        """
        Event for mirror check box
        """
        self.settings.setValue(self.MIRROR_KEY, self.mirror_joints)

    def create_joints_from_locators_clicked(self):
        """
        Event for Create Joints button
        """
        joint_root = create_joints_from_locator_hierarchy(mirror_joints=self.mirror_joints, axis=self.current_axis)
        orient_joints(joint_root=joint_root, recurse=True)

    def create_locators_from_joints_clicked(self):
        """
        Event for Create Locators button
        """
        create_locator_hierarchy_from_joints(mirror_joints=self.mirror_joints, axis=self.current_axis,
                                             size=self.current_size)

    def create_locator_at_selection_center_clicked(self):
        """
        Event for create locator button
        """
        selection = cmds.ls(sl=True)
        position = get_midpoint_from_transform(selection) if selection else POINT3_ORIGIN
        locator = create_locator(position=position, size=self.current_size)
        set_component_mode(ComponentType.object)
        cmds.select(locator)

    def create_pivot_locators_clicked(self):
        """
        Event for pivot locator button
        """
        create_pivot_locators(size=self.current_size)


class CharacterTools(GenericWidget):
    def __init__(self):
        super(CharacterTools, self).__init__('Character Tools', margin=4)
        self.rig_builder = self.add_widget(GroupBox('Rig Builder', RigBuilder()))
        self.add_button('Center Pivot', event=pivot_to_center, tool_tip='Center pivot')
        self.add_button('Match Pivot', event=match_pivot_to_last, tool_tip='Match pivot to last.')
        self.add_button('Mirror Limb Geometry', event=mirror_limbs)
        self.add_button('Orient Joints', event=self.orient_joints)
        self.add_button('Bind Skin', event=bind_skin, tool_tip='Bind joint hierarchy to model.')
        self.add_button('Bind Skin (Rigid Mode)', event=partial(bind_skin, True),
                        tool_tip='Bind joint hierarchy to model using single influences.')

    @staticmethod
    def orient_joints():
        """
        Set the joint orientations
        """
        with UndoStack('orient_joints'):
            orient_joints(recurse=True)


if __name__ == '__main__':
    tool = CharacterTools()
    tool.show()

