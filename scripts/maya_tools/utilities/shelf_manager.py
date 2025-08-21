"""Utils for shelves."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from typing import Callable, Sequence

from maya import cmds, mel
from PySide6.QtCore import QSettings

from core import DEVELOPER
from core.core_enums import Language
from core.core_paths import image_path

SHELF_LAYOUT = mel.eval("$tmpVar=$gShelfTopLevel")
SHELVES: list = cmds.shelfTabLayout(SHELF_LAYOUT, query=True, childArray=True)
SCRIPT_ICON: Path = image_path("script.png")
SHELF_CONFIG: Path = Path(__file__).parents[2] / "config" / "shelf_config.ini"


logging.basicConfig(format="$(levelname)s: $(message)s", level=logging.INFO)


class ShelfManager(ABC):
    """Class to handle Maya shelves."""

    def __init__(self, title: str) -> None:
        """Init."""
        self.title: str = title.replace(" ", "_")
        self.settings: QSettings = QSettings(DEVELOPER, title)
        self.panel_buttons = {}

    @abstractmethod
    def initialize_buttons(self) -> None:
        """Add buttons to the shelf."""

    @property
    def exists(self) -> bool:
        """Query if shelf exists."""
        return self.title in SHELVES

    @property
    def index(self) -> int:
        """Index of the shelf in the shelf list."""
        return SHELVES.index(self.title) + 1

    @property
    def buttons(self) -> list:
        """List of buttons in the shelf."""
        shelf_contents = cmds.shelfLayout(self.title, query=True, childArray=True)
        if shelf_contents is None:
            return []
        return  [x for x in shelf_contents if "shelfButton" in x]

    def add_button(self, label: str, icon: Path, command: Callable,
                   overlay_label: str = "", overwrite: bool = True) -> None:
        """Add a button to the shelf."""
        if label in self.buttons and overwrite:
            self.delete_button(label=label)
        cmds.shelfButton(label=label, image=icon,
                            parent=self.title, command=command,
                            overlayLabelBackColor=(0, 0, 0, 0),
                            imageOverlayLabel=overlay_label)

    def add_panel_button(self, label: str, overlay_label: str, linked_labels: Sequence,
                         state: bool = True) -> None:
        """Add a panel button to the shelf."""
        if label in self.buttons:
            self.delete_button(label=label)
        icon_true = image_path("panel_open.png")
        icon_false = image_path("panel_closed.png")
        self.panel_buttons[label] = {True: icon_true, False: icon_false,
                                      "linked": list(linked_labels)}
        state = state if state else self.settings.value(label, defaultValue=True)
        icon = icon_true if state else icon_false
        cmd = partial(self.toggle_icon_button, label)
        cmds.shelfButton(label=label, parent=self.title, command=cmd, image=icon,
                         overlayLabelBackColor=(0, 0, 0, 0),
                         imageOverlayLabel=overlay_label)

    def add_separator(self) -> None:
        """Add a separator to the current shelf."""
        cmds.setParent(self.title)
        cmds.separator(width=4, height=35, horizontal=False,
                       backgroundColor=(0.6, 0.6, 0.6), enableBackground=False)

    def add_toggle_button(self, label: str, icon_true: Path, icon_false: Path,
                          command: Callable | None = None,
                          linked_labels: Sequence = (),
                          state: bool = True) -> None:
        """Add a toggle button to the shelf."""
        if label in self.buttons:
            self.delete_button(label=label)

        self.panel_buttons[label] = {True: icon_true, False: icon_false,
                                      "linked": list(linked_labels)}

        def cmd() -> None:
            """Toggle button command."""
            self.toggle_icon_button(label)
            command() if command else None

        icon = icon_true if state else icon_false
        cmds.shelfButton(label=label, parent=self.title, command=cmd, image=icon)

    def create(self, set_focus: bool = True) -> None:
        """Create shelf if it doesn't exist."""
        self.delete()
        cmds.shelfLayout(self.title,  parent=SHELF_LAYOUT)
        self.initialize_buttons()
        self.update_panels()
        if set_focus:
            self.set_focus()

    def delete(self) -> None:
        """Delete the shelf."""
        if self.title in SHELVES:
            try:
                cmds.deleteUI(self.title)
            except RuntimeError as err:
                logging.error(f"Nope: {err}")

    def delete_button(self, label: str) -> None:
        """Remove a button from the shelf."""
        button = self.get_button(label=label)
        if button:
            cmds.deleteUI(button)
            if label in self.panel_buttons:
                self.panel_buttons.pop(label)

    def delete_buttons(self) -> None:
        """Delete all buttons."""
        for button in self.buttons:
            cmds.deleteUI(button)

    def get_button(self, label: str) -> str | None:
        """Get button by label."""
        return next((x for x in self.buttons if cmds.shelfButton(
            x, query=True, label=True) == label), None)

    def set_button_visibility(self, label: str, state: bool) -> None:  # noqa: FBT001
        """Set the visibility of a button."""
        button = self.get_button(label=label)
        if button:
            cmds.shelfButton(button, edit=True, visible=1 if state else 0)

    def set_focus(self) -> None:
        """Set the shelf focus."""
        if self.exists:
            cmds.shelfTabLayout(SHELF_LAYOUT, edit=True, selectTabIndex=self.index)

    @staticmethod
    def execute_script(script: str, language: Language = Language.python) -> None:
        """Execute a script."""
        if language is Language.python:
            exec(script)
        elif language is Language.mel:
            mel.eval(script)
        else:
            logging.info(f"Language not supported: {language}")


    def toggle_icon_button(self, label: str) -> bool | None:
        """Toggle an icon button."""
        button = self.get_button(label=label)
        if button:
            icon =  cmds.shelfButton(button, query=True, image=True)
            state = str(icon) == str(self.panel_buttons[label][True])
            self.settings.setValue(label, not state)
            cmds.shelfButton(button, edit=True,
                             image=self.panel_buttons[label][not state])
            for linked in self.panel_buttons[label]["linked"]:
                self.set_button_visibility(label=linked, state=not state)
            return not state
        return None

    def update_panels(self) -> None:
        """Update panels and linked buttons."""
        for label in self.panel_buttons:
            state = self.settings.value(label, "true") == "true"
            button = self.get_button(label=label)
            cmds.shelfButton(button, edit=True, image=self.panel_buttons[label][state])
            for linked in self.panel_buttons[label]["linked"]:
                self.set_button_visibility(label=linked, state=state)
