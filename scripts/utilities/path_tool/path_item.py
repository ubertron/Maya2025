from __future__ import annotations

import subprocess
from functools import partial
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QClipboard
from PySide6.QtWidgets import QWidget, QLineEdit, QSizePolicy, QApplication, QMenu

from clickable_label import ClickableLabel
from core import environment_utils, file_utils, logging_utils
from core.core_enums import Alignment
from core.core_paths import image_path
from core.file_utils import sanitize_path_string
from generic_widget import GenericWidget
from icon_button import IconButton
from path_dialog import PathDialog
from utilities.path_tool import TOOL_NAME, PathType, SOURCE_CONTROL_ROOT

LOGGER = logging_utils.get_logger(TOOL_NAME)


class PathItem(GenericWidget):
    """Widget to display/set a path."""

    updated = Signal(tuple or None)
    deleted = Signal(Path)
    button_width: int = 70
    script_extensions: list[str] = (".cfg", ".json", ".py", ".rtf", ".txt", ".yaml")

    def __init__(self, path: Path, parent_widget: QWidget) -> None:
        """Init."""
        super().__init__(alignment=Alignment.horizontal)
        self.parent_widget = parent_widget
        self.description_line_edit: QLineEdit = self.add_widget(QLineEdit())
        self.browse_button: IconButton = self.add_icon_button(
            icon_path=image_path("browse.png"), tool_tip="Browse...")
        self.path_label: ClickableLabel = self.add_widget(ClickableLabel())
        self.add_icon_button(icon_path=image_path("delete.png"),
                             tool_tip="Remove path", clicked=self.delete_button_clicked)
        self.path = path
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up ui."""
        self.description_line_edit.setPlaceholderText("Description...")
        self.description_line_edit.returnPressed.connect(self.description_updated)
        self.description_line_edit.setFixedWidth(200)
        self.path_label.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Preferred)
        self.path_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.path_label.clicked.connect(partial(self.context_menu, self.path))
        self.browse_button.clicked.connect(
            partial(self.browse_button_clicked, self.path))


    def browse_button_clicked(self, arg: Path) -> None:
        """Event for browse button."""
        dialog: PathDialog = PathDialog()

        if self.directory:
            dialog.text = arg.as_posix()
            dialog.directory = self.directory.as_posix()

        if dialog.exec() and dialog.path:
            self.path = dialog.path

    def open_button_clicked(self) -> None:
        """Event for open button."""
        if self.path.exists():
            if self.path_type is PathType.script:
                subprocess.Popen([NOTEPAD.as_posix(), self.path.as_posix()])  # noqa: S603
            elif self.is_maya_file and environment_utils.is_using_maya_python():
                from maya import cmds
                cmds.file(self.path.as_posix(), open=True, force=True)
            else:
                self.find_button_clicked()

    def open_in_code_button_clicked(self) -> None:
        """Event for open in code button."""
        if self.path.exists():
            subprocess.Popen([VS_CODE.as_posix(), self.path.as_posix()])  # noqa: S603


    def copy_button_clicked(self) -> None:
        """Event for copy button."""
        QApplication.clipboard().setText(str(self.path))

    def find_button_clicked(self) -> None:
        """Open the path in explorer."""
        self.parent_widget.info = f"Finding {self.path.name}"

        if not file_utils.open_in_finder(path=self.path):
            self.parent_widget.info += ": Nope"

    def delete_button_clicked(self) -> None:
        """Event for delete button."""
        self.deleted.emit(self.path)

    @property
    def description(self) -> str:
        """Description text."""
        return self.description_line_edit.text()

    @description.setter
    def description(self, value: str) -> None:
        self.description_line_edit.setText(value)

    @property
    def path(self) -> Path | None:
        """Current path."""
        return self._path

    @property
    def directory(self) -> Path | None:
        """Current directory."""
        if self.path:
            return self.path if self.path.is_dir() else self.path.parent
        return None

    @path.setter
    def path(self, value: Path) -> None:
        self._path = value
        if value:
            self.path_label.setText(f"{value.name} [{self.path_type.name}]")
            self.path_label.setToolTip(str(self.path))
            self.path_label.setStyleSheet(f"color: {self.path_type.color}")

            if not self.description:
                self.description = value.name
            self.updated.emit((self.path, self.description))
        else:
            self.path_label.setText("None")
            self.path_label.setToolTip("")
            self.updated.emit(None)

    @property
    def path_type(self) -> PathType:
        """The type of path."""
        if not self.path.exists():
            return PathType.missing
        if self.path.suffix in self.script_extensions:
            return PathType.script
        if "." in self.path.name:
            return PathType.local_file
        return PathType.local_dir

    def description_updated(self) -> None:
        """Event for update of description label."""
        # check description to see if it's a path
        if SOURCE_CONTROL_ROOT in Path(self.description).parents:
            self.path = Path(self.description)
            self.description = self.path.name
        else:
            self.description = sanitize_path_string(self.description)

        if self.is_location(self.description):
            self.path = Path(self.description)
            self.description = self.path.name

        self.description = self.path.name
        self.updated.emit((self.path, self.description))
        self.path_label.clicked.connect(partial(self.context_menu, self.path))

    @property
    def is_using_maya_python(self) -> bool:
        """Currently using Maya."""
        return environment_utils.is_using_maya_python()

    @property
    def is_maya_file(self) -> bool:
        """Path is Maya file."""
        return self.path.suffix in (".ma", ".mb")

    def context_menu(self, *args: any) -> QWidget:
        """Context menu."""
        path, point = args
        if path:
            menu: QMenu = QMenu()
            menu.addAction(path.name)
            menu.addSeparator()

            is_maya_file = self.is_maya_file and environment_utils.is_using_maya_python()

            if self.path_type is PathType.script or is_maya_file:
                menu.addAction(QAction("Open", self, triggered=self.open_button_clicked))

            if self.path_type is PathType.script:
                menu.addAction(QAction("Open In VS Code", self, triggered=self.open_in_code_button_clicked))

            menu.addAction(QAction("Find...", self, triggered=self.find_button_clicked))
            menu.addAction(QAction("Copy Path To Clipboard", self, triggered=self.copy_button_clicked))
            menu.addSeparator()
            menu.addAction(QAction("Delete path", self, triggered=self.delete_button_clicked))
            menu.exec(point)

    @property
    def is_workspace_path(self) -> bool:
        """Is path in workspace."""
        return VE_APPLE_PROJECT_ROOT in self.path.parents

    @property
    def is_depot_path(self) -> bool:
        """Is path is depot."""
        return HERC_ROOT in self.path.parents

    @staticmethod
    def is_location(value: str) -> bool:
        """Is path a location."""
        return (
            value[0].isalpha()
            and value[1] == ":"
            and value[2] in ("\\", "/")
        )

    def copy_herc_path(self) -> None:
        """Event for copy herc path action."""
        clipboard: QClipboard = QClipboard()

        if self.is_workspace_path:
            herc_path = HERC_ROOT.joinpath(self.path.relative_to(VE_APPLE_PROJECT_ROOT))
            clipboard.setText(herc_path.as_posix())
            msg = f"Herc path: {herc_path.as_posix()}"
            LOGGER.info(msg)
        else:
            msg = f"No valid herc path for {self.path.name}"
            LOGGER.info(msg)
