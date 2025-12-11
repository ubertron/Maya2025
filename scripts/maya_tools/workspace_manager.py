"""Utils to handle a Maya project."""
from __future__ import annotations

import logging
import os

from maya import cmds, mel
from pathlib import Path

from ams.ams_paths import SOURCE_ART, PROJECT_NAME, PROJECT_ROOT
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__, level=logging.DEBUG)


class WorkspaceManager:
    """Class to handle the Maya project workspace."""

    def __init__(self, workspace_root: Path = SOURCE_ART):
        self.workspace_root = workspace_root

    def __repr__(self):
        return (
            f"Workspace root: {self.workspace_root}"
        )

    @property
    def workspace(self) -> Path:
        """Set the project workspace."""
        return Path(cmds.workspace(query=True, rootDirectory=True))

    @workspace.setter
    def workspace(self, path: Path):
        if path.exists():
            mel.eval(f'setProject "{path.as_posix()}"')
            LOGGER.info(f'Project set to {path}')
        else:
            msg = f"{path} not found."
            raise NotADirectoryError(msg)

    def set_workspace(self):
        """Set the project workspace.

        Arguments:
            path {Path | None} if no arg supplied, env path is used
        """
        self.workspace = self.workspace_root

if __name__ == "__main__":
    wm = WorkspaceManager()
    print(wm)