import os

from pathlib import Path
from qtpy.QtWidgets import QFileDialog, QLineEdit
from qtpy.QtCore import Signal
from typing import Optional

from core.core_enums import Alignment
from widgets.generic_dialog import GenericDialog


class DirectoryBrowser(GenericDialog):
    directory_set = Signal(str)

    def __init__(self, default_directory: Optional[Path] = None):
        super(DirectoryBrowser, self).__init__(title='Directory Browser', alignment=Alignment.horizontal)
        self.button = self.add_button('Browse...', tool_tip='Click to browse for path', event=self.browse_clicked)
        self.line_edit: QLineEdit = self.add_widget(QLineEdit())
        self.line_edit.setPlaceholderText('<enter path>')
        self.default_directory: Path = default_directory if default_directory else Path(__file__).parents[2]

    @property
    def text(self) -> str:
        return self.line_edit.text()

    def browse_clicked(self):
        d = QFileDialog.getExistingDirectory(self, 'Browse for directory', self.default_directory.as_posix(),
                                             QFileDialog.ShowDirsOnly)
        if d:
            self.line_edit.setText(d)
            self.directory_set.emit(d)


if __name__ == '__main__':
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    browser = DirectoryBrowser()
    browser.resize(600, browser.sizeHint().height())
    browser.show()
    sys.exit(app.exec())
