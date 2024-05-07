import platform

from maya import mel
from typing import List


def get_environment_variables(variable_name: str, log: bool = False) -> List[str]:
    sep = ':' if platform.system() == 'Darwin' else ';'
    paths = mel.eval('getenv %s' % variable_name).split(sep)
    paths.sort(key=lambda x: x.lower())

    if log:
        print(f"Paths for {variable_name}:\n" + "\n".join([x for x in paths]))
    return paths


def format_environment_variables():
    get_environment_variables('PYTHONPATH', True)
    get_environment_variables('MAYA_SCRIPT_PATH', True)
    get_environment_variables('MAYA_PLUGIN_PATH', True)
    get_environment_variables('MAYA_MODULE_PATH', True)


if __name__ == "__main__":
    format_environment_variables()
