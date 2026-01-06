import os
import platform

from pathlib import Path
from maya import mel, OpenMayaUI
from typing import List
from PySide6.QtWidgets import QMainWindow
from shiboken6 import wrapInstance

from core import DARWIN_STR


MAYA_MAIN_WINDOW = wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QMainWindow)


def is_using_mac_osx() -> bool:
    """
    Returns true if using Mac OSX
    :return:
    """
    return platform.system() == DARWIN_STR


def get_environment_variables(variable_name: str, log: bool = False) -> List[str]:
    sep = ':' if is_using_mac_osx() else ';'
    paths = mel.eval(f'getenv {variable_name}').split(sep)
    paths.sort(key=lambda x: x.lower())

    if log:
        print(f"Paths for {variable_name}:\n" + "\n".join([x for x in paths]))
    return paths


def format_environment_variables():
    get_environment_variables('PYTHONPATH', True)
    get_environment_variables('MAYA_SCRIPT_PATH', True)
    get_environment_variables('MAYA_PLUGIN_PATH', True)
    get_environment_variables('MAYA_MODULE_PATH', True)
    get_environment_variables('MAYA_APP_DIR', True)


def get_env_variable(variable: str = "MAYA_PLUG_IN_PATH"):
    # Get the value of MAYA_PLUG_IN_PATH
    plugin_path_str = os.getenv(variable)
    env_paths = []

    if plugin_path_str:
        # Split the string into individual paths using the platform-specific separator
        # Semicolon (;) on Windows, colon (:) on macOS and Linux
        separator = ";" if os.name == 'nt' else ":"
        paths = plugin_path_str.split(separator)
        for path in paths:
            env_paths.append(Path(path.strip()))
    else:
        print("MAYA_PLUG_IN_PATH is not explicitly set in the environment variables.")
        print("Maya will still search default locations like the user's plug-ins folder.")
    return sorted(env_paths)


MAYA_APP_DIR: Path = Path(get_environment_variables(variable_name='MAYA_APP_DIR')[0])


if __name__ == "__main__":
    variable = "MAYA_PLUG_IN_PATH"
    result = get_env_variable(variable)

    print(f"{variable} directories:")
    for x in result:
        print(f"* {x}")
