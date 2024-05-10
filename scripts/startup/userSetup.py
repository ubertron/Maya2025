import logging
import os
import hashlib
import configparser

from pathlib import Path
from maya import cmds


def main():
    cmds.scriptEditorInfo(clearHistory=True)    # Debug only: comment out to view full startup log
    script_path = Path.home().joinpath('Dropbox/Technology/Python3/Projects/Maya2025/scripts/startup')
    logging.info(f">>> Maya2025 Project userSetup.py in {script_path}")
    # Get latest from source control


cmds.evalDeferred(main, lowestPriority=True)
