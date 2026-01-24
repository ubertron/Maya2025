import enum

try:
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import QPoint, Qt, Signal
    from PySide6.QtGui import QMouseEvent
    PYSIDE_VERSION = 6
except ImportError:
    from PySide2.QtWidgets import QLabel
    from PySide2.QtCore import QPoint, Qt, Signal
    from PySide2.QtGui import QMouseEvent
    PYSIDE_VERSION = 2
from widgets.generic_widget import GenericWidget


class ClickableLabel(QLabel):
    clicked: Signal = Signal(QPoint)
    clicked_right: Signal = Signal(QPoint)

    def __init__(self, *args, global_context: bool = True, button: enum = Qt.MouseButton.LeftButton):
        super(ClickableLabel, self).__init__(*args)
        assert type(button).__name__ == 'MouseButton', 'Please supply Qt.MouseButton enum'
        self.global_context: bool = global_context
        self.button: enum = button

    def mousePressEvent(self, event):
        # PySide2/6 compatibility: globalPos() vs globalPosition()
        if PYSIDE_VERSION == 6:
            global_position = event.globalPosition().toPoint()
        else:
            global_position = event.globalPos()

        local_position = self.window().mapFromGlobal(global_position)
        position = global_position if self.global_context else local_position

        if event.button() == Qt.MouseButton.RightButton:
            self.clicked_right.emit(position)
        elif event.button() == self.button:
            self.clicked.emit(position)


class TestWidget(GenericWidget):
    def __init__(self):
        super(TestWidget, self).__init__('Clickable Label Test Widget')
        label = self.add_widget(ClickableLabel('This is a label', global_context=False))
        self.resize(320, 40)
        label.clicked.connect(self.label_clicked)

    @staticmethod
    def label_clicked(args):
        print(f'Label clicked: {args}')


if __name__ == '__main__':
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        from PySide2.QtWidgets import QApplication

    app = QApplication()
    widget = TestWidget()
    widget.show()
    app.exec()
