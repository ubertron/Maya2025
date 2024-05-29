import platform
from pathlib import Path

from maya import mel
from typing import List
from core import DARWIN_STR


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


MAYA_APP_DIR: Path = Path(get_environment_variables(variable_name='MAYA_APP_DIR')[0])


if __name__ == "__main__":
    format_environment_variables()
