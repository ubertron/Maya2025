import logging

from datetime import datetime
from maya import OpenMayaUI, cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from typing import Callable, Optional
from inspect import getsource

from core.core_enums import Side
from core.point_classes import Point2
from maya_tools.maya_environment_utils import MAYA_MAIN_WINDOW
from widgets.generic_widget import GenericWidget


class MayaDockableWidget(MayaQWidgetDockableMixin, GenericWidget):
    """A GenericWidget which is dockable in the Maya interface"""
    def __init__(self, title: str = "", size: Optional[Point2] = None):
        super(MayaDockableWidget, self).__init__(title=title, size=size, parent=MAYA_MAIN_WINDOW)


def delete_existing_workspace_control(instance: object):
    """Delete existing instances of the workspace control before creating"""
    control_name = f'{instance.objectName()}WorkspaceControl'

    if cmds.workspaceControl(control_name, exists=True):
        logging.info(f'>>> Found {control_name}')
        cmds.workspaceControl(control_name, edit=True, close=True)
        cmds.deleteUI(control_name, control=True)


def restore(widget_class: Callable):
    """
    Restore widget when Maya restarts
    :param widget_class:
    """
    workspace_control = OpenMayaUI.MQtUtil.getCurrentParent()
    widget_class._instance = widget_class()
    logging.info(f">>> Restore script for {widget_class.__name__}")
    pointer = OpenMayaUI.MQtUtil.findControl(widget_class._instance.objectName())
    OpenMayaUI.MQtUtil.addWidgetToMayaLayout(int(pointer), int(workspace_control))


def generate_ui_script(instance: object, import_module: str) -> str:
    """
    Generate restore script for dockable widget class instance
    :param instance:
    :param import_module:
    :return:
    """
    widget_class = instance.__class__.__name__
    script = "from widgets import maya_dockable_widget\n"
    script += f"from {import_module} import {widget_class}\n"
    script += f"maya_dockable_widget.restore({widget_class})\n"

    return script


class ExampleDockableWidget(MayaDockableWidget):
    TITLE = "Example Dockable Widget"

    def __init__(self):
        super(ExampleDockableWidget, self).__init__(title=self.TITLE, size=Point2(320, 80))
        self.label = self.add_label(f"{self.__class__.__name__} label", side=Side.center)
        self.add_button("Get time", event=self.button_clicked)

    def button_clicked(self):
        self.label.setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


if __name__ == "__main__":
    dockable_widget = ExampleDockableWidget()
    delete_existing_workspace_control(instance=dockable_widget)
    ui_script = generate_ui_script(instance=dockable_widget, import_module='widgets.maya_dockable_widget')
    # dockable_widget.show(dockable=True, floating=False, area='left', uiScript=ui_script)
    dockable_widget.show(dockable=True, floating=True, uiScript=ui_script)

