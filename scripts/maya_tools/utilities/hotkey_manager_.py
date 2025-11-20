r"""Util to handle hotkeys.

Hotkey sets are saved here: ~\Documents\maya\2022\prefs\hotkeys
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Sequence

from maya import cmds
from pathlib import Path

from core import logging_utils
from core.core_enums import Language, ModifierKey

LOGGER = logging_utils.get_logger()


def get_hotkey_sets() -> list[str]:
    """List of hotkey sets."""
    result = cmds.hotkeySet(query=True, hotkeySetArray=True)
    return result if result else []


class HotkeyManager(ABC):
    """Hotkey manager."""

    def __init__(self, hotkey_set: str, force: bool = True) -> None:
        """Init."""
        self.hotkey_set = hotkey_set
        self.force = force
        if hotkey_set in get_hotkey_sets():
            cmds.hotkeySet(hotkey_set, edit=True, current=True)
        else:
            cmds.hotkeySet(hotkey_set, current=True)
        msg = f"Hotkey set: {hotkey_set}"
        LOGGER.info(msg)

    @abstractmethod
    def apply(self) -> None:
        """Apply the hotkeys: set the hotkeys in this function."""

    def _set_hotkey(self, name: str, annotation: str, command: str, hotkey: str,  # noqa: PLR0913
                   modifier_keys: Sequence[ModifierKey] = (),
                   language: Language = Language.python,
                   log_level: int = logging.DEBUG,
                   category: str = "Custom Scripts") -> None:
        """Add hotkey to hotkey set.

        hotkey: single ascii key | Up, Down, Right, Left, Home, End, Page_Up,
        Page_Down, Insert, Return, Space, F1 to F12
        """
        if log_level:
            LOGGER.setLevel(log_level)
        if language is Language.python:
            command = f'python("{command}");'
        if cmds.runTimeCommand(name, query=True, exists=True):
            if self.force:
                cmds.runTimeCommand(name, edit=True, delete=True)
            else:
                msg = f"Command already exists: {name}"
                raise AttributeError(msg)
        cmds.runTimeCommand(
            name, annotation=annotation, category=category,
            commandLanguage=language.name, command=command)
        cmds.nameCommand(
            name, annotation=annotation, command=command, sourceType=language.name)
        cmds.hotkey(
            keyShortcut=hotkey,
            altModifier=ModifierKey.alt in modifier_keys,
            ctrlModifier=ModifierKey.control in modifier_keys,
            commandModifier=ModifierKey.command in modifier_keys,
            name=name)
        modifier_string = " + " + ", ".join(x.name for x in modifier_keys) \
            if modifier_keys else ""
        msg = f"Hotkey added: {name} | {language.name} | {hotkey}{modifier_string}"
        LOGGER.debug(msg)

    def export(self, path: Path):
        """Export hotkeys."""
        path.parent.mkdir(parents=True, exist_ok=True)
        cmds.hotkeySet(self.hotkey_set, edit=True, export=path.as_posix())

    def import_from_path(self, path: Path):
        """Import hotkeys."""
        if path.exists():
            cmds.hotkeySet(self.hotkey_set, edit=True, ip=path.as_posix())