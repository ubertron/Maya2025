"""hotkey_manager.py"""
from __future__ import annotations

import json
import logging

from dataclasses import dataclass
from maya import cmds

from core import logging_utils
from core.core_enums import Language, ModifierKey
from core.core_paths import CONFIG_DIR, HOTKEYS_CONFIG, STARTUP_DIR

LOGGER = logging_utils.get_logger(name=__name__, level=logging.DEBUG)

@dataclass
class Hotkey:
    """Maya hotkey."""

    name: str
    annotation: str
    command: str
    hotkey: str
    modifiers: list[ModifierKey]
    language: Language
    category: str

    def __repr__(self) -> str:
        modifier_string = ", ".join(x.name for x in self.modifiers)
        return (
            f"Name: {self.name}: {self.annotation}\n"
            f"Command: {self.command}\n"
            f"Hotkey: {self.hotkey}\n"
            f"Modifiers: {modifier_string}\n"
            f"Language: {self.language}\n"
            f"Category: {self.category}\n"
        )

    def apply(self, force: bool = False):
        """Set the hotkey."""
        if cmds.runTimeCommand(self.name, query=True, exists=True):
            if force:
                cmds.runTimeCommand(self.name, edit=True, delete=True)
            else:
                msg = f"Command already exists: {self.name}"
                raise AttributeError(msg)
        cmds.runTimeCommand(
            self.name,
            annotation=self.annotation,
            category=self.category,
            commandLanguage=self.language.name,
            command=self.cmd)
        cmds.nameCommand(
            self.name,
            annotation=self.annotation,
            command=self.cmd,
            sourceType=self.language.name)
        cmds.hotkey(
            keyShortcut=self.hotkey,
            altModifier=ModifierKey.alt in self.modifiers,
            ctrlModifier=ModifierKey.control in self.modifiers,
            commandModifier=ModifierKey.command in self.modifiers,
            name=self.name)
        modifier_string = " + " + ", ".join(x.name for x in self.modifiers) \
            if self.modifiers else ""
        msg = f"Hotkey added: {self.name} | {self.language.name} | {self.hotkey}{modifier_string}"
        print(msg)

    @property
    def cmd(self) -> str:
        return self.command if self.language is Language.mel else f'python("{self.command}");'

    @property
    def dict_(self):
        return {
            "annotation": self.annotation,
            "command": self.command,
            "hotkey": self.hotkey,
            "modifiers": [x.name for x in self.modifiers],
            "language": self.language,
            "category": self.category,
        }


@dataclass
class HotkeySet:
    """Class to handle hotkeys."""

    name: str
    hotkeys: list[Hotkey]

    def __repr__(self) -> str:
        return f"HotkeySet: {self.name}\n" +  "\n".join(str(x) for x in self.hotkeys)

    @property
    def dict_(self):
        return {x.name: x.dict_ for x in self.hotkeys}

    @property
    def path(self) -> Path:
        return CONFIG_DIR / f"{self.name}.mhk"

    def apply(self, force: bool = False):
        if self.name in get_hotkey_sets():
            cmds.hotkeySet(self.name, edit=True, current=True)
        else:
            cmds.hotkeySet(self.name, current=True)
        msg = f"Hotkey set: {self.name}"
        print(msg)
        for hotkey in self.hotkeys:
            hotkey.apply(force=force)

    def export_set(self):
        """
        Export the hotkeys to the stated path
        """
        cmds.hotkeySet(self.name, edit=True, export=self.path)


class HotkeyManager:
    """Hotkey Manager."""

    def __init__(self) -> None:
        self.hotkey_sets = []
        self._load_config()

    def _load_config(self) -> None:
        """Load config."""
        if HOTKEYS_CONFIG.exists():
            with HOTKEYS_CONFIG.open(mode="r") as f:
                data = json.load(f)
        else:
            LOGGER.exception(f"{HOTKEYS_CONFIG} does not exist")
        for name, hotkey_data in data.items():
            hotkeys = []
            for hotkey, keys in hotkey_data.items():
                hotkeys.append(Hotkey(
                    name=hotkey,
                    annotation=keys.get("annotation"),
                    command=keys.get("command"),
                    hotkey=keys.get("hotkey"),
                    modifiers=[ModifierKey[key] for key in keys.get("modifiers")],
                    language=Language[keys.get("language")],
                    category=keys.get("category"),
                ))
            self.hotkey_sets.append(HotkeySet(name=name, hotkeys=hotkeys))

    @property
    def data(self) -> dict:
        return {x.name: x.dict_ for x in self.hotkey_sets}

    def apply(self, force: bool = False) -> None:
        """Apply the hotkeys.

        Arguments:
            force (bool, optional): Force apply hotkeys. Defaults to False.
        """
        for hotkey_set in self.hotkey_sets:
            hotkey_set.apply(force=force)

    def export(self):
        """Export hotkey sets to mhk files."""
        for hotkey_set in self.hotkey_sets:
            hotkey_set.export_set()

    def format_hotkey_sets(self):
        """Print out the hotkeys."""
        for hotkey_set in self.hotkey_sets:
            print(hotkey_set)

    def save_config(self) -> None:
        """Save config."""
        for hotkey_set, hotkey_data in self.data.items():
            print(hotkey_set)
            for hotkey, hotkey_attrs in hotkey_data.items():
                print(f"{hotkey}: {hotkey_attrs}")


def get_hotkey_sets() -> list[str]:
    """List of hotkey sets."""
    result = cmds.hotkeySet(query=True, hotkeySetArray=True)
    return result if result else []