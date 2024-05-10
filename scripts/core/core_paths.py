import platform
import sys
from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).parents[2]
ICONS: Path = PROJECT_ROOT.joinpath('icons')
REQUIREMENTS: Path = PROJECT_ROOT.joinpath('requirements.txt')
MAYA_REQUIREMENTS: Path = PROJECT_ROOT.joinpath('maya_requirements.txt')
SITE_PACKAGES: Path = PROJECT_ROOT.joinpath('site-packages')
MAYA_APP_DIRECTORY: Path = Path('/Applications/Autodesk/maya2025')
MAYA_INTERPRETER_PATH: Path = MAYA_APP_DIRECTORY.joinpath('Maya.app/Contents/bin/mayapy')
MAYA_CONFIG: Path = PROJECT_ROOT.joinpath('bin/maya_config.ini')
MODELS_FOLDER: Path = PROJECT_ROOT.joinpath('models')
SCENES_FOLDER: Path = PROJECT_ROOT.joinpath('scenes')


def icon_path(file_name: str) -> Path:
    return ICONS.joinpath(file_name)


def query_path(path_constant: Path):
    print(f'Path: {path_constant} Exists? {path_constant.exists()}')


if __name__ == '__main__':
    # print(PROJECT_ROOT, PROJECT_ROOT.exists())
    # print(icon_path('base_female.png').exists())
    query_path(PROJECT_ROOT)
    query_path(icon_path('base_female.png'))
    query_path(SITE_PACKAGES)
    query_path(MAYA_REQUIREMENTS)
    query_path(MAYA_INTERPRETER_PATH)
