"""Path Tool for Rubicon."""
from __future__ import annotations

import json
import logging
import subprocess
from enum import Enum
from functools import partial
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QScrollArea,
    QWidget,
)

from core import environment_utils
from core import logging_utils
from core.core_paths import image_path
from core.file_utils import sanitize_path_string
from core.version_info import VersionInfo
from utilities.path_tool import TOOL_NAME
from utilities.path_tool.path_item import PathItem
from utilities.path_tool.path_tool_help import PathToolHelp
from widgets.button_bar import ButtonBar
from widgets.generic_widget import GenericWidget
from widgets.path_dialog import PathDialog

# MAYA: Path = Path(r"C:\Program Files\Autodesk\Maya2022\bin\maya.exe")
# VS_CODE: Path = Path(r"C:\Program Files\Microsoft VS Code\Code.exe")
DEFAULT_DATA: Path = Path(__file__).parent / "data" / "path_tool.json"
PATH_TOOL_ICON: Path = image_path("path_tool.png")
VERSIONS = (
    VersionInfo(name=TOOL_NAME, version="1.0", codename="lotus", info="Initial Pyside6 port"),
)

LOGGER = logging_utils.get_logger(TOOL_NAME)


class PathToolMode(Enum):
    """Enum for mod."""

    path = 0
    description = 1

    @staticmethod
    def get_by_name(name: str) -> Enum:
        """Get enum by value."""
        return next((x for x in PathToolMode if x.name == name), None)


class PathTool(GenericWidget):
    """Path Tool."""

    description_key = "description"

    def __init__(self, parent_widget: QWidget | None=None) -> None:
        """Init."""
        super().__init__(title=VERSIONS[-1].title)
        self.settings = QSettings("Sandbox", TOOL_NAME)
        self.parent_widget = parent_widget
        self.mode = PathToolMode.get_by_name(
            name=self.settings.value("mode", "path"))
        self.button_bar: ButtonBar = self.add_widget(ButtonBar())
        self.button_bar.add_icon_button(
            icon_path=image_path("refresh.png"),
            tool_tip="Refresh", clicked=self.update_path_widget)
        self.button_bar.add_icon_button(
            icon_path=image_path("new.png"),
            tool_tip="New", clicked=self.new_button_clicked)
        self.button_bar.add_icon_button(
            icon_path=image_path("open.png"), tool_tip="Open",
            clicked=self.open_button_clicked)
        self.button_bar.add_icon_button(
            icon_path=image_path("save.png"), tool_tip="Save As",
            clicked=self.save_as_button_clicked)
        self.button_bar.add_icon_button(
            icon_path=image_path("add.png"), tool_tip="Add Path",
            clicked=self.add_path_clicked)
        self.button_bar.add_icon_button(
            icon_path=image_path("data.png"), tool_tip="Open Data",
            clicked=self.open_data_clicked)
        self.add_current_scene_button = self.button_bar.add_icon_button(
            icon_path=image_path("maya.png"), tool_tip="Add Current Scene",
            clicked=self.add_current_scene_button_clicked)
        self.button_bar.add_icon_button(icon_path=image_path("sort_description.png"), tool_tip="Sort By Description", clicked=partial(
            self.set_mode, PathToolMode.description))
        self.button_bar.add_icon_button(icon_path=image_path("sort_path.png"), tool_tip="Sort By Path", clicked=partial(
            self.set_mode, PathToolMode.description))
        self.button_bar.add_stretch()
        self.button_bar.add_icon_button(
            icon_path=image_path("help.png"), tool_tip="Help",
            clicked=self.help_button_clicked)
        self.path_label: QLabel = self.add_label()
        self.path_widget: GenericWidget = GenericWidget()
        scroll_area: QScrollArea = self.add_widget(QScrollArea())
        scroll_area.setWidget(self.path_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.info_label = self.add_label("Ready...")
        self.data_file: Path = Path(self.settings.value("data_file", DEFAULT_DATA))
        self.help_window: PathToolHelp = PathToolHelp(self)
        self.add_path_dialog: PathDialog = PathDialog()
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up ui."""
        self.info_label.setAlignment(Qt.AlignLeft)
        self.path_label.setAlignment(Qt.AlignLeft)
        self.setStyleSheet("textSize=10")
        self.setWindowIcon(QIcon(QPixmap(PATH_TOOL_ICON.as_posix())))
        if environment_utils.is_using_standalone_python():
            self.add_current_scene_button.setEnabled(False)

    def save_paths(self) -> None:
        """Save paths to json."""
        with self.data_file.open("w") as f:
            json.dump(self.paths, f)

    def new_button_clicked(self) -> None:
        """Event for new button."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save New File", self.data_file.parent.as_posix(),
            "Json (*.json)",
        )

        if file_path:
            if not Path(file_path).exists():
                with Path(file_path).open("w") as f:
                    json.dump({}, f)

            self.data_file = Path(file_path)
            self.update_path_widget()

    def open_button_clicked(self) -> None:
        """Event for open button."""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Json (*.json)")
        dialog.setDirectory(self.data_file.parent.as_posix())

        if dialog.exec():
            self.data_file = Path(dialog.selectedFiles()[0])

    def save_as_button_clicked(self) -> None:
        """Event for save as button."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save New File", self.data_file.parent.as_posix(),
            "Json (*.json)",
        )

        if file_path:
            data = self.data
            self.data_file = Path(file_path)
            self.data = data
            self.save_data()
            self.settings.setValue("data_file", file_path)
            self.update_window_title()
            self.update_path_widget()

    @property
    def data_file(self) -> Path:
        """Path of the data file."""
        return self._data_file

    @data_file.setter
    def data_file(self, value: Path) -> None:
        self._data_file = value if value.exists() else DEFAULT_DATA
        self.path_label.setText(f"Path Data File: {self._data_file.stem}")

        if self.data_file.exists():
            with self.data_file.open("r") as f:
                self.data = json.load(f)
            self.settings.setValue("data_file", value)
        else:
            self.data = {}

        self.update_window_title()
        self.update_path_widget()

    @property
    def data(self) -> dict:
        """Data dictionary."""
        return self._data

    @data.setter
    def data(self, value: dict) -> None:
        self._data = value
        self.paths = self.data.keys() if self.data else []
        self.descriptions = [
            x[self.description_key] for x in self.data.values()] if self.data else []

    @property
    def info(self) -> str:
        """Text of the info_label."""
        return self.info_label.text()

    @info.setter
    def info(self, value: str) -> None:
        self.info_label.setText(value)

    @property
    def tool_title(self) -> str:
        """Tool title."""
        return VERSIONS[-1].title

    def set_mode(self, value: PathToolMode) -> None:
        """Set the mode."""
        self.mode = value
        self.settings.setValue("mode", value.name)
        self.update_path_widget()

    def update_window_title(self) -> None:
        """Update window title."""
        if self.parent_widget is not None:
            self.parent_widget.setWindowTitle(
                f"{self.parent_widget.tool_title} - {self.data_file.name}")
        else:
            self.setWindowTitle(f"{self.tool_title} - {self.data_file.name}")

    def add_path_clicked(self) -> None:
        """Event for add path button."""
        add_path_dialog = PathDialog()

        if add_path_dialog.exec() and add_path_dialog.text:
            path = Path(sanitize_path_string(add_path_dialog.text))
            self.add_path_item(path=path)

    def add_path_item(self, path: Path) -> PathItem:
        """Add a path widget."""
        self.info = path.name
        path_item = PathItem(path=path, parent_widget=self)
        if self.mode is PathToolMode.path:
            path_list = self.paths + [path_item.path]
            path_list.sort(key=lambda x: x.as_posix().lower())
            index = path_list.index(path_item)
        else:
            descriptions = self.descriptions + [path_item.description]
            descriptions.sort(key=lambda x: x.lower())
            index = descriptions.index(path_item.description)
        self.path_widget.layout().insertWidget(index, path_item)
        path_item.description_line_edit.setText(path.name)
        path_item.updated.connect(self.update_paths)
        path_item.deleted.connect(self.delete_path)
        path_item.description_updated()
        return path_item

    def add_current_scene_button_clicked(self) -> None:
        """Event for add current scene button."""
        if environment_utils.is_using_maya_python():
            from maya import cmds
            scene_path = cmds.file(query=True, sceneName=True)
            if not scene_path:
                self.info = "No scene open."
                return
            scene_path = Path(scene_path)
            QApplication.clipboard().setText(scene_path.as_posix())
            if scene_path in self.paths:
                description = self.get_description_from_path(scene_path)
                self.info = f"Path exists already: {description} - {scene_path.name}"
            else:
                self.add_path_item(path=scene_path)

    def get_description_from_path(self, path: Path) -> str | None:
        """Find the description of a path."""
        return self.descriptions[self.paths.index(path)] if path in self.paths else None

    def _sort_paths(self) -> None:
        """Sort the paths and descriptions."""
        data = [(self.paths[i], self.descriptions[i]) for i in range(len(self.paths))]
        if self.mode is PathToolMode.path:
            data.sort(key=lambda x: x[0].as_posix().lower())
        else:
            data.sort(key=lambda x: x[1].lower())
        self.paths = [x[0] for x in data]
        self.descriptions = [x[1] for x in data]

    def update_path_widget(self) -> None:
        """Populate the path widget with PathItem objects."""
        if self.data_file.exists():
            with self.data_file.open("r") as f:
                self.data = json.load(f)
        else:
            self.data = {}
            self.save_data()

        self.path_widget.clear_layout()
        self._sort_paths()

        for idx, path in enumerate(self.paths):
            widget: PathItem = self.path_widget.add_widget(
                PathItem(path=Path(path), parent_widget=self))
            widget.updated.connect(self.update_paths)
            widget.deleted.connect(self.delete_path)
            widget.description = self.descriptions[idx]

        self.path_widget.add_stretch()
        self.info = "Ready..."

    def update_paths(self)-> None:
        """Update the data and the json file."""
        self.paths = [x.path for x in self.path_widget.widgets if x.path]
        self.descriptions = [x.description for x in self.path_widget.widgets if x.path]
        data = {}

        for i in range(len(self.paths)):
            data[self.paths[i].as_posix()] = {
                self.description_key: self.descriptions[i]}

        self.data = data
        self.save_data()
        LOGGER.debug("Path data updated.")

    def save_data(self) -> None:
        """Save data."""
        self.data_file.parent.mkdir(exist_ok=True, parents=True)

        with self.data_file.open("w") as f:
            json.dump(self.data, f, indent=True)

    def delete_path(self, arg: Path) -> None:
        """Delete a path."""
        if arg not in self.paths:
            self.update_path_widget()
            return
        index = self.paths.index(arg)
        item = self.path_widget.layout().takeAt(index)
        widget = item.widget()
        widget.setParent(None)
        self.update_paths()

    @property
    def paths(self) -> list[Path]:
        """List of paths."""
        return self._paths

    @paths.setter
    def paths(self, value: list[Path | str]) -> None:
        self._paths = [Path(x) for x in value]

    def open_data_clicked(self) -> None:
        """Event for Open Rubicon Data button."""
        if environment_utils.is_using_windows():
            notepad: Path = Path(r"C:\Windows\System32\notepad.exe")
            subprocess.Popen([notepad.as_posix(), self.data_file.as_posix()])
        else:
            subprocess.run(["open", "-a", "TextEdit", self.data_file.as_posix()], check=True)

    def help_button_clicked(self) -> None:
        """Event for help button."""
        self.info = "Help..."
        self.help_window.show()


if __name__ == "__main__":
    # Set Windows application context for icon
    if environment_utils.is_using_windows():
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.myproduct.subproduct.version")

    import qdarktheme
    app = QApplication()
    qdarktheme.setup_theme()
    tool = PathTool()
    tool.show()
    app.exec()