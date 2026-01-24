import sys

try:
    from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
    from PySide6.QtCore import QMargins
except ImportError:
    from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout
    from PySide2.QtCore import QMargins


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
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QLabel
    except ImportError:
        from PySide2.QtWidgets import QApplication, QWidget, QLabel

    app = QApplication(sys.argv)
    widget = QWidget()
    widget.setLayout(VBoxLayout())
    widget.layout().addWidget(QLabel('Hello'))
    widget.show()
    app.exec()
