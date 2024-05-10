import pkg_resources

from pathlib import Path
from typing import List


MAYA_PLUGINS_FOLDER: Path = Path('/Applications/Autodesk/maya2025/plug-ins')


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
    format_installed_packages()
    # list_user_setup_script()
