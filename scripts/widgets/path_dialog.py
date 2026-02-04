"""Dialog for getting paths."""
from __future__ import annotations

from pathlib import Path

from qtpy.QtWidgets import QFileDialog, QLineEdit
from core.core_enums import Alignment
from core.core_paths import image_path
from widgets.generic_dialog import GenericDialog
from widgets.generic_widget import GenericWidget


class PathDialog(GenericDialog):
    """Add path dialog."""

    def __init__(self, directory: Path | str | None = None) -> None:
        """Init."""
        super().__init__("Path Tool: Add Path")
        path_bar: GenericWidget = self.add_widget(
            GenericWidget(alignment=Alignment.horizontal))
        path_bar.add_icon_button(icon_path=image_path("browse.png"),
                             tool_tip="Browse...", clicked=self.browse_button_clicked)
        self.line_edit: QLineEdit = path_bar.add_widget(QLineEdit())
        button_bar: GenericWidget = self.add_widget(
            GenericWidget(alignment=Alignment.horizontal))
        button_bar.row_mode = True
        button_bar.add_button("OK", clicked=self.accept)
        button_bar.add_button("Cancel", clicked=self.close)
        self.directory = directory
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up ui."""
        self.setFixedHeight(self.sizeHint().height())
        self.resize(240, self.sizeHint().height())


    def browse_button_clicked(self) -> None:
        """Event for browse button."""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Files (*.*)")

        if self.directory:
            dialog.setDirectory(self.directory.as_posix())

        if dialog.exec():
            self.line_edit.setText(dialog.selectedFiles()[0])

    @property
    def text(self) -> str:
        """Line edit text."""
        return self.line_edit.text()

    @text.setter
    def text(self, value: str) -> None:
        self.line_edit.setText(value)

    @property
    def path(self) -> Path | None:
        """Path."""
        return Path(self.text) if self.text else None

    @property
    def directory(self) -> Path | None:
        """Directory."""
        return self._directory

    @directory.setter
    def directory(self, value: Path | str | None) -> None:
        self._directory = Path(value) if value else None

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PathDialog()
    window.show()
    app.exec()
