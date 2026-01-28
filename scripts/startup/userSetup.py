"""userSetup.py from startup directory

Directory must be specified in the tools module accessible by the module path.
"""
import logging

from maya import cmds
from pathlib import Path

from core import logging_utils
from startup import pip_utils

LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)
_DEBUG_MODE = False


def setup_maya():
    """Function sets up Maya session."""
    from maya_tools.ui import shelf_utils
    from maya_tools.ui import hotkey_manager
    # from startup.robotools_hotkeys import RobotoolsHotkeys
    if _DEBUG_MODE:
        cmds.scriptEditorInfo(clearHistory=True)    # Debug only: comment out to view full startup log
    path = Path.home() / "Dropbox/Technology/Python3/Projects/Maya2025/scripts/startup"
    LOGGER.info(f">>> Maya2025 Project userSetup.py in {path}")
    LOGGER.info(f">>> Installing required packages")
    pip_utils.install_requirements()
    LOGGER.info(f">>> Initializing shelves")
    shelf_utils.ShelfManager().build()
    LOGGER.info(f">>> Initializing hotkeys")
    hotkey_manager.HotkeyManager().apply(force=True)


cmds.evalDeferred(setup_maya, lowestPriority=True)
