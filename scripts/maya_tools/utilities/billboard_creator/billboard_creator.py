from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtWidgets import QDoubleSpinBox, QFileDialog, QSizePolicy

from core import DEVELOPER, image_utils
from core.core_enums import Axis
from core.core_paths import image_path
from core.version_info import VersionInfo
from core.core_enums import Position
from maya_tools.utilities.billboard_creator import billboard_creator_utils
from widgets.grid_widget import GridWidget
from widgets.image_label import ImageLabel

DEFAULT_IMAGE = image_path("help.png")
TOOL_NAME = "Billboard Creator"
VERSIONS = [
    VersionInfo(name=TOOL_NAME, version="0.1", codename="stingray", info="initial release")
]


class BillboardCreator(GridWidget):
    no_image_label = "No image selected"
    size_key = "size"
    image_path_key = "image_path"
    height_key = "height"
    width_key = "width"

    def __init__(self):
        super().__init__(title=VERSIONS[-1].title)
        self.settings = QSettings(DEVELOPER, TOOL_NAME)
        self.image_label: ImageLabel = self.add_widget(ImageLabel(path=DEFAULT_IMAGE), row=0, column=0, col_span=2)
        self.browse_button = self.add_button("Browse...", row=1, column=0, event=self.browse_button_clicked)
        self.path_label = self.add_label(
            self.no_image_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, row=1, column=1)
        self.add_label(text="Width", row=2, column=0)
        self.width_spin_box: QDoubleSpinBox = self.add_widget(QDoubleSpinBox(), row=2, column=1)
        self.add_label(text="Height", row=3, column=0)
        self.height_spin_box: QDoubleSpinBox = self.add_widget(QDoubleSpinBox(), row=3, column=1)
        self.add_button("Create", row=4, column=0, col_span=2, event=self.create_button_clicked)
        self._setup_ui()

    def _setup_ui(self):
        self.browse_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.image_label.setMinimumHeight(64)
        self.setMinimumWidth(320)
        width = self.settings.value(self.width_key, None)
        width = float(width) if width else 1.0
        height = self.settings.value(self.height_key, None)
        height = float(height) if height else 1.0
        self.width_spin_box.setValue(width)
        self.height_spin_box.setValue(height)
        self.width_spin_box.setRange(0.1, 1000)
        self.height_spin_box.setRange(0.1, 1000)
        self.evaluate_height()
        width, height = [int(x) for x in (self.settings.value(self.size_key, [320, 320]))]
        self.resize(QSize(width, height))
        settings_image_path = self.settings.value(self.image_path_key)
        if settings_image_path and Path(settings_image_path).exists():
            self.path = Path(settings_image_path)
        self.width_spin_box.valueChanged.connect(self.evaluate_height)

    @property
    def path(self) -> Path | None:
        return Path(self.path_label.text()) if self.path_label.text() != self.no_image_label else None

    @path.setter
    def path(self, value: Path | None):
        self.path_label.setText(value.as_posix() if value else self.no_image_label)
        self.image_label.path = value if value else DEFAULT_IMAGE
        print(f">>> {self.image_label.path} {value}")
        if value:
            self.settings.setValue(self.image_path_key, value.as_posix())
            self.evaluate_height()

    @property
    def height(self) -> int:
        return self.height_spin_box.value()

    @height.setter
    def height(self, value):
        self.height_spin_box.setValue(value)
        self.settings.setValue(self.height_key, value)

    @property
    def width(self) -> int:
        return self.width_spin_box.value()

    @width.setter
    def width(self, value):
        self.width_spin_box.setValue(value)
        self.settings.setValue(self.width_key, value)

    def browse_button_clicked(self):
        # Open a file dialog to select an existing file
        # Parameters: parent, caption, initial_directory, filter
        image_value = self.settings.value(self.image_path_key, None)
        start_dir = Path(image_value).parent.as_posix() if image_value and Path(image_value).parent.exists() else "."
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            start_dir,  # Start in the current directory
            "Images (*.bmp *.gif *.jpeg *.jpg *.png *.tga *.tif *.tiff *.xpm)"
        )
        self.path = Path(filename) if filename else None

    def create_button_clicked(self):
        """Event for create button."""
        billboard_creator_utils.create_billboard(path=self.path, width=self.width, height=self.height, axis=Axis.z)

    def evaluate_height(self):
        if self.path:
            image_size = image_utils.get_image_size(path=self.path)
            self.height = self.width * image_size[1] / image_size[0]

    def resizeEvent(self, event):
        """Resize event."""
        self.settings.setValue(self.size_key, [self.size().width(), self.size().height()])
        super().resizeEvent(event)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import qdarktheme

    app = QApplication()
    qdarktheme.setup_theme()
    widget = BillboardCreator()
    widget.show()
    app.exec_()