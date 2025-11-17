"""Class to handle Maya shelves."""
from __future__ import annotations

import contextlib
import json
import logging
import threading

from functools import partial
from importlib import reload
from pathlib import Path
from PySide6.QtWidgets import QLayout, QWidget
from PySide6.QtCore import QSettings
from shiboken6 import wrapInstance

from core.version_info import VersionInfo
from core.core_enums import Language
from core import core_paths; reload(core_paths)
from core.core_paths import image_path, CONFIG_DIR
from core import logging_utils, DEVELOPER
from maya_tools import display_utils

with contextlib.suppress(ImportError):
    from maya import cmds, mel, OpenMayaUI, utils


TOOL_NAME = "Shelf Manager"
VERSION = (
    VersionInfo(name=TOOL_NAME, version="1.0", codename="dead cat", info="initial release"),
    VersionInfo(name=TOOL_NAME, version="2.0", codename="dead monkey", info="update for Maya 2026"),
    VersionInfo(name=TOOL_NAME, version="2.1", codename="dolphin",
                info="New version which builds the shelf from a json data file")
)
LOGGER = logging_utils.get_logger(__name__, level=logging.DEBUG)
SHELF_DATA = CONFIG_DIR / "shelves.json"
SHELF_LAYOUT = mel.eval("$tmpVar=$gShelfTopLevel")


class Shelf:
    """Class to handle custom Maya shelves."""

    panel_open_icon = image_path("panel_open.png")
    panel_closed_icon = image_path("panel_closed.png")
    script_icon: Path = image_path("script.png")

    def __init__(self, title: str, data: dict):
        self.settings = QSettings(DEVELOPER, f"{title}_shelf")
        self.title = title
        self.data = data
        self.panel_buttons = {}

    @property
    def buttons(self) -> list:
        """List of buttons in the shelf."""
        shelf_contents = cmds.shelfLayout(self.title, query=True, childArray=True)
        if shelf_contents is None:
            return []
        return  [x for x in shelf_contents if "shelfButton" in x]

    @property
    def exists(self) -> bool:
        """Query if shelf exists."""
        return self.title in self.shelves

    @property
    def index(self) -> int:
        """Index of the shelf in the shelf list."""
        return self.shelves.index(self.title) + 1

    @property
    def shelf_layout(self):
        """Get the layout object."""
        result = mel.eval("$tmpVar=$gShelfTopLevel")
        return result

    @property
    def shelves(self) -> list[str]:
        """Get the names of the shelves."""
        return cmds.shelfTabLayout(self.shelf_layout, query=True, childArray=True)

    @property
    def widget(self):
        ptr = OpenMayaUI.MQtUtil.findControl(self.title)
        if ptr is not None:
            return wrapInstance(int(ptr), QWidget)
        return None

    def add_button(self, label: str, icon: Path, command: str, source_type: Language, overlay_label: str = "",
                   overwrite: bool = True) -> None:
        """Add a button to the shelf."""
        if label in self.buttons and overwrite:
            self.delete_button(label=label)
        cmds.shelfButton(
            label=label, image=icon, parent=self.title, command=command, overlayLabelBackColor=(0, 0, 0, 0),
            imageOverlayLabel=overlay_label, sourceType=source_type.name)

    def add_panel_button(self, label: str, state: bool | None=None, linked_labels: list[str] = None) -> None:
        """Add a panel button."""
        self.panel_buttons[label] = {True: self.panel_open_icon, False: self.panel_closed_icon,
                                      "linked": list(linked_labels)}
        state = state if state else self.settings.value(label, defaultValue=True)
        icon = self.panel_open_icon if state else self.panel_closed_icon
        cmd = partial(self.toggle_icon_button, label)
        short_label = self.shorten_label(label=label)
        cmds.shelfButton(
            label=label, parent=self.title, command=cmd, image=icon, overlayLabelBackColor=(0, 0, 0, 0),
            imageOverlayLabel=short_label)

    @staticmethod
    def shorten_label(label: str) -> str:
        label = label.title()
        return "".join(c for c in label if c not in "aeiou ")[:5] if len(label) > 5 else label

    def create(self):
        """Build the shelf."""
        self.delete()
        cmds.shelfLayout(self.title,  parent=SHELF_LAYOUT)
        for panel in self.data:
            self.add_panel_button(label=panel, state=None, linked_labels=self.data[panel].keys())
            for label, button_data in self.data[panel].items():
                icon = image_path(file_name=button_data["icon"])
                if icon:
                    overlay_label = ""
                else:
                    icon = self.script_icon
                    overlay_label = self.shorten_label(label=label)
                source_type = Language.__members__.get(button_data["language"])
                self.add_button(
                    label=label,
                    icon=icon,
                    command=button_data["script"],
                    source_type=source_type,
                    overlay_label=overlay_label,
                )
        self.update_panels()

    def delete(self) -> None:
        """Delete the shelf."""
        if self.title in self.shelves:
            try:
                cmds.deleteUI(self.title)
            except RuntimeError as err:
                LOGGER.exception(f"Tried : {err}")

    def get_button(self, label: str) -> str | None:
        """Get button by label."""
        return next((x for x in self.buttons if cmds.shelfButton(x, query=True, label=True) == label), None)

    def set_button_visibility(self, label: str, state: bool) -> None:  # noqa: FBT001
        """Set the visibility of a button."""
        button = self.get_button(label=label)
        if button:
            cmds.shelfButton(button, edit=True, visible=1 if state else 0)

    def set_focus(self) -> None:
        """Set the shelf focus."""
        if self.exists:
            cmds.shelfTabLayout(SHELF_LAYOUT, edit=True, selectTabIndex=self.index)

    def toggle_icon_button(self, label: str) -> bool | None:
        """Toggle an icon button."""
        button = self.get_button(label=label)
        if button:
            icon = cmds.shelfButton(button, query=True, image=True)
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
            # state = self.settings.value(label, "true") == "true"
            state = self.settings.value(label, True)
            button = self.get_button(label=label)
            cmds.shelfButton(button, edit=True, image=self.panel_buttons[label][state])
            for linked in self.panel_buttons[label]["linked"]:
                self.set_button_visibility(label=linked, state=state)


class ShelfManager:
    """Class to handle custom Maya shelves."""
    def __init__(self):
        assert SHELF_DATA.exists(), f"Cannot find shelf data file: {SHELF_DATA}"
        with SHELF_DATA.open(mode="r") as f:
            self.data = json.load(f)

    @property
    def shelf_layout(self):
        """Get the layout object."""
        return get_shelf_layout()

    @property
    def names(self) -> list[str]:
        """Get the names of the shelves."""
        return cmds.shelfTabLayout(SHELF_LAYOUT, query=True, childArray=True)

    def build(self) -> None:
        """Build shelves from a data file.

        Needs to be threaded, otherwise the routine deletes itself
        """
        def routine():
            msg = f"Creating shelves: {', '.join(self.shelves)}"
            LOGGER.info(msg)
            for shelf, shelf_data in self.data.items():
                Shelf(title=shelf, data=shelf_data).create()

        def target_thread():
            utils.executeInMainThreadWithResult(routine)

        my_thread = threading.Thread(target=target_thread, daemon=True)
        my_thread.start()

    def delete(self) -> None:
        """Remove shelves specified in the data file."""
        shelves = self.data.keys()
        LOGGER.info(f"Deleting shelves: {', '.join(shelves)}")
        for shelf in shelves:
            cmds.deleteUI(shelf)

    def get_shelf_index(self, shelf: str) -> int | None:
        """Get the index of a named shelf."""
        return self.names.index(shelf) + 1 if shelf in self.names else None

    def save(self):
        """Save shelf data."""
        with SHELF_DATA.open(mode="w") as f:
            json.dump(self.data, f, indent=4)

    def set_focus(self, shelf: str) -> None:
        """Set the shelf focus."""
        if index := self.get_shelf_index(shelf=shelf):
            cmds.shelfTabLayout(SHELF_LAYOUT, edit=True, selectTabIndex=index)
        else:
            cmds.warning(f"Shelf {shelf} not found.")

    @property
    def shelves(self) -> list[str]:
        return list(self.data.keys())


def get_current_shelf() -> str | None:
    """
    Returns the name of the currently active shelf in Maya.
    """
    return cmds.tabLayout(SHELF_LAYOUT, query=True, selectTab=True) if SHELF_LAYOUT else None


def get_shelf_layout() -> str:
    return mel.eval('global string $gShelfTopLevel; $temp = $gShelfTopLevel;')


def get_shelf_layout_widget() -> QLayout:
    """Get the layout object."""
    ptr = OpenMayaUI.MQtUtil.findLayout(SHELF_LAYOUT)
    return wrapInstance(int(ptr), QLayout)


def set_current_shelf(shelf_name: str) -> None:
    """
    Sets the current active shelf in Maya by its name.

    Args:
        shelf_name (str): The name of the shelf to activate.
    """
    if cmds.tabLayout(SHELF_LAYOUT, exists=True):
        if cmds.shelfLayout(shelf_name, exists=True):
            cmds.tabLayout(SHELF_LAYOUT, edit=True, selectTab=shelf_name)
        else:
            display_utils.info_message(text=f"Shelf '{shelf_name}' does not exist.")
    else:
        display_utils.info_message(text="Could not find the global shelf top level UI element.")




if __name__ == "__main__":
    # build_shelves()
    # delete_shelves()
    shelf_manager = ShelfManager()
    shelf_manager.build()
    # shelf_manager.set_focus(shelf="Novotools")
    #shelf_manager.save()