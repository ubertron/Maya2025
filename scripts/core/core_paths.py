import platform
import sys
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parents[2]
IMAGE_DIR: Path = PROJECT_ROOT.joinpath('images')
REQUIREMENTS: Path = PROJECT_ROOT.joinpath('requirements.txt')
MAYA_REQUIREMENTS: Path = PROJECT_ROOT.joinpath('maya_requirements.txt')
SITE_PACKAGES: Path = PROJECT_ROOT.joinpath('site-packages')
AUTODESK_DIR = Path('/Applications/Autodesk')
MAYA_VERSIONS = ("maya2025", "maya2026")
MAYA_APP_DIR: Path = next(AUTODESK_DIR / y for y in MAYA_VERSIONS if AUTODESK_DIR.joinpath(y).exists())
MAYA_INTERPRETER_PATH: Path = MAYA_APP_DIR.joinpath('Maya.app/Contents/bin/mayapy')
MAYA_CONFIG: Path = PROJECT_ROOT.joinpath('bin/maya_config.ini')
MODELS_DIR: Path = PROJECT_ROOT.joinpath('models')
SCENES_DIR: Path = PROJECT_ROOT.joinpath('scenes')
PRESETS_DIR: Path = PROJECT_ROOT.joinpath('scripts/startup/presets')


def image_path(file_name: str) -> Path:
    return IMAGE_DIR.joinpath(file_name)


def query_path(path_constant: Path):
    print(f'Path: {path_constant} Exists? {path_constant.exists()}')


if __name__ == '__main__':
    # print(PROJECT_ROOT, PROJECT_ROOT.exists())
    # print(icon_path('base_female.png').exists())
    query_path(PROJECT_ROOT)
    query_path(image_path('base_female.png'))
    query_path(SITE_PACKAGES)
    query_path(MAYA_REQUIREMENTS)
    query_path(MAYA_APP_DIR)
    query_path(MAYA_INTERPRETER_PATH)
