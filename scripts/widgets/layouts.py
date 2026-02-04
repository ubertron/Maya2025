import sys

from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout
from qtpy.QtCore import QMargins


class VBoxLayout(QVBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(VBoxLayout, self).__init__()
        self.setContentsMargins(QMargins(margin, margin, margin, margin))
        self.setSpacing(spacing)


class HBoxLayout(QHBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(HBoxLayout, self).__init__()
        self.setContentsMargins(QMargins(margin, margin, margin, margin))
        self.setSpacing(spacing)


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication, QWidget, QLabel

    app = QApplication(sys.argv)
    widget = QWidget()
    widget.setLayout(VBoxLayout())
    widget.layout().addWidget(QLabel('Hello'))
    widget.show()
    app.exec()
