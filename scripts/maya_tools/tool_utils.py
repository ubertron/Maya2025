"""
Example of tool launching:
from maya_tools.utilities import character_tools
launch_utility(class_name=character_tools.CharacterTools, object_name='Character Tools')
"""

import logging

from maya.OpenMayaUI import MQtUtil
from PySide6.QtWidgets import QMainWindow
from shiboken6 import wrapInstance
from typing import Type

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

MAYA_MAIN_WINDOW: QMainWindow = wrapInstance(int(MQtUtil.mainWindow()), QMainWindow)


def get_utility(utility_class: Type, object_name) -> object or None:
    """
    Looks for utility under Maya
    :param utility_class:
    :param object_name:
    :return:
    """
    result = MQtUtil.findControl(object_name)

    if result:
        return wrapInstance(int(result), utility_class)


def launch_utility(utility_class: Type, object_name: str, **kwargs):
    """
    Script launches a utility
    :param utility_class:
    :param object_name:
    :param kwargs:
    """
    utility = get_utility(utility_class=utility_class, object_name=object_name)
    
    if utility:
        logging.debug(f'Utility found: {utility}')
    else:
        utility = utility_class(**kwargs)
        logging.debug(f'Utility not found. Creating new instance: {utility}')
    
    utility.show()
