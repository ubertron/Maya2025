import enum

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from widgets.generic_widget import GenericWidget


class ClickableLabel(QLabel):
    clicked: Signal = Signal(QPoint)

    def __init__(self, *args, global_context: bool = True, button: enum = Qt.MouseButton.LeftButton):
        super(ClickableLabel, self).__init__(*args)
        assert type(button).__name__ == 'MouseButton', 'Please supply Qt.MouseButton enum'
        self.global_context: bool = global_context
        self.button: enum = button

    def mousePressEvent(self, event):
        global_position = event.globalPosition().toPoint()
        local_position = self.window().mapFromGlobal(global_position)
        position = global_position if self.global_context else local_position

        if event.button() == self.button:
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
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    widget = TestWidget()
    widget.show()
    app.exec()
