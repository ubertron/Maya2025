"""
from maya_tools.tool_utils import launch_utility
from shared_utils import mock_utility
from shared_utils.mock_utility import mockUtility

launch_utility(module=mock_utility, utility_class=mockUtility.MockUtility, label_a='rod', label_c='freddy')
"""
import logging

from maya.OpenMayaUI import MQtUtil
from PySide6.QtWidgets import QWidget
from shiboken6 import wrapInstance
from typing import Type
from importlib import reload

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

MAYA_MAIN_WINDOW: QWidget = wrapInstance(int(MQtUtil.mainWindow()), QWidget)


def getWidget(widget_class: Type[QWidget], first_only: bool = True) -> Type[QWidget] or list[Type[QWidget]] or None:
    """
    Finds instances of the passed widget classes in Maya
    @param widget_class: the widget class
    @param first_only: set to true to only pass the first instance
    @return:
    """
    for x in MAYA_MAIN_WINDOW.children():
        print(x)
    if first_only:
        return next((x for x in MAYA_MAIN_WINDOW.children() if type(x) is widget_class), None)
    else:
        return [x for x in MAYA_MAIN_WINDOW.children() if type(x) is widget_class]


def launch_utility(module: Type, utility_class: Type, **kwargs):
    """
    Handles the reloading of utilities avoiding duplication
    Reload is necessary because Maya's garbage collection can nuke classes
    :param module:
    :param utility_class:
    :param kwargs:
    """
    utility = getWidget(widget_class=utility_class)
    print('MELONS', utility, utility_class)

    if utility:
        print('POOT')
        utility.deleteLater()
        reload(module)

    utility = utility_class(**kwargs)
    utility.show()
