import platform
import sys
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parents[2]
SCRIPTS_DIR = Path(__file__).parent.parent  # scripts directory
MAYA_REQUIREMENTS: Path = PROJECT_ROOT / 'maya_requirements.txt'
AUTODESK_DIR = Path('/Applications/Autodesk')
CONFIG_DIR = PROJECT_ROOT / 'config'
HOTKEYS_DATA: Path = CONFIG_DIR / 'hotkeys.json'
SHELF_DATA: Path = CONFIG_DIR / 'shelves.json'
IMAGE_DIR: Path = PROJECT_ROOT / 'images'
ICON_DIR: Path = IMAGE_DIR / 'icons'
MAYA_CONFIG: Path = CONFIG_DIR / 'maya_config.ini'
MODELS_DIR: Path = PROJECT_ROOT / 'models'
PRESETS_DIR: Path = PROJECT_ROOT.joinpath('scripts/startup/presets')
REQUIREMENTS: Path = PROJECT_ROOT / 'requirements.txt'
SCENES_DIR: Path = PROJECT_ROOT / 'scenes'
SITE_PACKAGES: Path = PROJECT_ROOT / 'site-packages'
SCRIPT_ICON: Path = ICON_DIR / 'python.png'  # Default icon for script shelf buttons
PLUGINS_DIR: Path = PROJECT_ROOT / 'plugins'
ROBOTOOLS_PLUGINS_DIR: Path = PLUGINS_DIR / 'robotools'
STARTUP_DIR = SCRIPTS_DIR / 'startup'
MAYA_VERSIONS = ("maya2022", "maya2023", "maya2024", "maya2025", "maya2026")
MAYA_APP_DIR: Path = next((AUTODESK_DIR / y for y in MAYA_VERSIONS if AUTODESK_DIR.joinpath(y).exists()), None)
MAYA_INTERPRETER_PATH: Path = MAYA_APP_DIR.joinpath('Maya.app/Contents/bin/mayapy') if MAYA_APP_DIR else None
MAYA_WINDOWS: Path = Path(r"C:\Program Files\Autodesk\Maya2022\bin\maya.exe")
VS_CODE_WINDOWS: Path = Path(r"C:\Program Files\Microsoft VS Code\Code.exe")


def image_path(file_name: str) -> Path:
    """Get the path of a file from the project image directory."""
    return next((x for x in IMAGE_DIR.rglob(file_name)), None)


def query_path(path_constant: Path):
    print(f'Path: {path_constant} Exists? {path_constant.exists()}')


if __name__ == '__main__':
    print(image_path("mirror_geometry.png"))
    print(image_path("mirror_geometry_.png"))
    print(CONFIG_DIR, CONFIG_DIR.exists())
