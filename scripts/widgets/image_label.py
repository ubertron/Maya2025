"""Resizable image label widget."""
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPixmap, QTransform
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


DALEK: Path = Path.home() / "Dropbox/Technology/Python3/Projects/Maya2025/images/dalek.png"


class ImageLabel(QLabel):
    """Resizable image label widget."""

    def __init__(self, path: Path) -> None:
        """Init."""
        super().__init__()
        self.setWindowTitle(path.name)
        self.path: Path = path
        self.setFrameStyle(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: Path) -> None:
        self._path = path
        self.pixmap: QPixmap = QPixmap(path.as_posix())
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001, ARG002
        """Paint event."""
        size = self.size()
        painter: QPainter = QPainter(self)
        point = QPoint(0, 0)
        scaled_pix = self.pixmap.scaled(
            size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        point.setX((size.width() - scaled_pix.width()) / 2)
        point.setY((size.height() - scaled_pix.height()) / 2)
        painter.drawPixmap(point, scaled_pix)


class TestWidget(QWidget):
    """Test widget."""

    def __init__(self, path: Path) -> None:
        """Init."""
        super().__init__()
        self.setWindowTitle(path.name)
        self.setLayout(QVBoxLayout())
        button_bar: QWidget = QWidget()
        button_bar.setLayout(QVBoxLayout())
        button_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        rotate_button: QPushButton = QPushButton("Rotate Image")
        button_bar.layout().addWidget(rotate_button)
        self.layout().addWidget(button_bar)
        self.image_label: ImageLabel = ImageLabel(path=path)
        self.layout().addWidget(self.image_label)
        rotate_button.clicked.connect(self.rotate_button_clicked)

    def rotate_button_clicked(self) -> None:
        """Event for rotate button."""
        transform = QTransform()
        transform.rotate(90)
        rotated_pixmap = self.image_label.pixmap.transformed(transform)
        self.image_label.setPixmap(rotated_pixmap)





if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    widget = TestWidget(path=DALEK)
    # widget = ImageLabel(path=DALEK)
    widget.show()
    app.exec_()