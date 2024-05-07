import logging
import os

from pathlib import Path
from maya import cmds


def main():
    cmds.scriptEditorInfo(clearHistory=True)    # TEMP! Makes my life easier while I'm setting up the environment
    script_path = Path.home().joinpath('Dropbox/Technology/Python3/Projects/Maya2025/scripts/startup')
    logging.info(f">>> Maya2025 Project userSetup.py in {script_path}")


cmds.evalDeferred(main, lowestPriority=True)
