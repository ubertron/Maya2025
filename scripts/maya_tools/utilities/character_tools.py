from functools import partial
from importlib import reload
from maya import cmds
from PySide6.QtWidgets import QCheckBox

from widgets import generic_widget; reload(generic_widget)
from maya_tools import helpers; reload(helpers)
from maya_tools import node_utils; reload(node_utils)
from maya_tools import rigging_utils; reload(rigging_utils)
from maya_tools import character_utils; reload(character_utils)

from core.point_classes import POINT3_ORIGIN
from core.core_enums import Alignment
from maya_tools.helpers import get_midpoint, create_locator, create_pivot_locators, get_selected_locators
from maya_tools.node_utils import ComponentType, set_component_mode, pivot_to_center, match_pivot_to_last, \
    get_locators
from maya_tools.character_utils import mirror_limbs
from maya_tools.rigging_utils import create_joints_from_locator_hierarchy
from widgets.float_input_widget import FloatInputWidget
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.group_box import GroupBox


class LocatorCreator(GridWidget):
    def __init__(self):
        super(LocatorCreator, self).__init__(title='Locator Creator')
        self.add_label('Locator Scale: ', 0, 0)
        self.numeric_input = self.add_widget(FloatInputWidget(0.1, 10.0), 0, 1)
        self.add_button('Create Locator At Selection Center', 1, 0, 1, 2, event=self.create_locator_clicked,
                        tool_tip='Create locator at the center of selected components')
        self.numeric_input.setText(str(1.0))
        self.add_button('Create Locators From Pivots', row=2, column=0, col_span=2, event=self.pivot_locators_clicked,
                        tool_tip='Create locators at selected pivot positions')

    @property
    def locator_size(self) -> float:
        return float(self.numeric_input.text())
    
    def create_locator_clicked(self):
        """
        Event for create locator button
        """
        selection = cmds.ls(sl=True)
        position = get_midpoint(selection) if selection else POINT3_ORIGIN
        locator = create_locator(position=position, size=self.locator_size)
        set_component_mode(ComponentType.object)
        cmds.select(locator)

    def pivot_locators_clicked(self):
        """
        Event for pivot locator button
        """
        create_pivot_locators(size=self.locator_size)


class CharacterTools(GenericWidget):
    def __init__(self):
        super(CharacterTools, self).__init__('Character Tools', margin=4)
        self.add_widget(GroupBox('Locator Creator', LocatorCreator()))
        self.add_button('Auto-Parent Locators', event=auto_parent_locators,
                        tool_tip='Create a hierarchy from selected locators')
        build_widget = self.add_widget(GenericWidget(alignment=Alignment.horizontal, margin=0, spacing=4))
        build_widget.add_button('Build Rig From Locators', event=self.build_rig_clicked,
                                tool_tip='Build a rig from the locator hierarchy')
        self.mirror_check_box: QCheckBox = build_widget.add_widget(QCheckBox('Mirror Joints'))
        self.add_button('Center Pivot', event=pivot_to_center, tool_tip='Center pivot')
        self.add_button('Match Pivot', event=match_pivot_to_last, tool_tip='Match pivot to last')
        self.add_button('Mirror Limb Geometry', event=mirror_limbs)
        self.add_button('Delete locators', event=partial(cmds.delete, get_locators()))

    def build_rig_clicked(self):
        create_joints_from_locator_hierarchy(mirror_joints=self.mirror_check_box.isChecked())


def auto_parent_locators():
    locators = get_selected_locators()

    if len(locators) > 1:
        for i in range(0, len(locators) - 1):
            print(locators[i])
            cmds.parent(locators[i], locators[i + 1])


def place_locator_in_centroid(size: float = 1.0):
    """
    Creates a locator in the center of the selection
    :param size:
    """
    assert len(cmds.ls(sl=True)), 'Select geometry'
    center = get_midpoint(cmds.ls(sl=True))
    create_locator(position=center, size=size)


def get_top_node(node):
    """
    Finds the top node in a hierarchy
    :param node:
    :return:
    """
    assert cmds.objExists(node), f'Node not found: {node}'
    parent = cmds.listRelatives(node, parent=True, fullPath=True)

    return node if parent is None else get_top_node(parent[0])
    

tool = CharacterTools()
tool.show()

# cmds.select('geo')
# selection = cmds.ls(sl=True, tr=True)
# if len(selection) == 1:
#     limb_nodes = character_utils.get_limb_nodes(selection[0])
#     print(limb_nodes)
