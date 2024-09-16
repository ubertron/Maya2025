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
        # utility = utility_class(**kwargs)
        utility = utility_class()
        logging.debug(f'Utility not found. Creating new instance: {utility}')
    
    utility.show()


def launch_script(module_name: str, script_name: str, class_name: str, object_name: str, keyword_args: str = None):
    """
    Creates a launch script for a utility
    :param module_name:
    :param script_name:
    :param class_name:
    :param object_name:
    :param keyword_args:
    :return:
    """
    script = 'from maya_tools.tool_utils import launch_utility\n'
    script += f'from {module_name} import {script_name}\n'
    keyword_args = f', {keyword_args}' if keyword_args else ''
    script += f'\nlaunch_utility(utility_class={script_name}.{class_name}, object_name="{object_name}{keyword_args}")\n'

    return script


if __name__ == '__main__':
    from pyperclip import copy
    script_ = launch_script(module_name='maya_tools.utilities', script_name='character_tools',
                            class_name='CharacterTools', object_name='Character Tools')
    copy(script_)
