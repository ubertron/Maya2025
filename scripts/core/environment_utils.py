import os
import pkg_resources
import platform
import sys

from pathlib import Path
from typing import List

from core.core_enums import PythonPlatform, OperatingSystem


MAYA_PLUGINS_FOLDER: Path = Path('/Applications/Autodesk/maya2025/plug-ins')
PYTHON_397 = '3.9.7'
# PYTHON_PLATFORM = 'python'
# MAYA_PLATFORM = 'maya'
# UNREAL_PLATFORM = 'unrealeditor'


def get_python_version() -> str:
    """
    Finds the version of Python as a string
    :return: str
    """
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"


def get_python_platform() -> PythonPlatform:
    """
    Finds the platform of Python as a string
    :return: str
    """
    return PythonPlatform.get_by_value(Path(sys.executable).stem.lower())


def is_using_maya_python() -> bool:
    """
    Determine if code is being used in a Maya environment
    :return: bool
    """
    return get_python_platform().name == PythonPlatform.maya.name


def is_using_standalone_python() -> bool:
    """
    Determine if code is being used in a standalone environment
    :return: bool
    """
    return get_python_platform() is PythonPlatform.standalone


def is_using_unreal_editor_python() -> bool:
    """
    Determine if code is being used in an Unreal environment
    :return: bool
    """
    return get_python_platform() is PythonPlatform.unreal


def get_operating_system() -> OperatingSystem:
    """
    Get operating system
    :return:
    """
    return OperatingSystem.get_by_value(platform.system())


def is_using_mac_os() -> bool:
    """
    Determine if using Mac OS
    :return:
    """
    return get_operating_system() is OperatingSystem.mac


def is_using_windows() -> bool:
    """
    Determinf if using Windows OS
    :return:
    """
    return get_operating_system() is OperatingSystem.windows


def list_user_setup_script() -> List[Path]:
    """
    Finds all userSetup.py files in the Maya plug-ins folders
    :return:
    """
    all_files = [x for x in MAYA_PLUGINS_FOLDER.glob('**/*') if x.is_file()]
    print('\n'.join(str(x) for x in all_files if x.name == 'userSetup.py'))
    return all_files


def format_installed_packages():
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted([f"{i.key}=={i.version}" for i in installed_packages])
    print('\n'.join(installed_packages_list))


if __name__ == '__main__':
    # format_installed_packages()
    # list_user_setup_script()
    print(get_operating_system())
    print(is_using_mac_os())
