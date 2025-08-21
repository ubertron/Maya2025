import logging

from pathlib import Path
from maya import cmds


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def main():
    cmds.scriptEditorInfo(clearHistory=True)    # Debug only: comment out to view full startup log
    path = Path.home() / "Dropbox/Technology/Python3/Projects/Maya2025/scripts/startup"
    logging.info(f">>> Maya2025 Project userSetup.py in {path}")
    # Get latest from source control


cmds.evalDeferred(main, lowestPriority=True)
