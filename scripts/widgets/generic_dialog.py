from qtpy.QtWidgets import QDialog, QHBoxLayout, QPushButton, QLabel, QWidget
from qtpy.QtCore import QPoint, Qt

from typing import Optional, Callable

from core.core_enums import Alignment
from widgets.layouts import HBoxLayout, VBoxLayout


class GenericDialog(QDialog):
    def __init__(self, title: str = '', position: Optional[QPoint] = None, modal: bool = True,
                 alignment=Alignment.vertical, parent: Optional[QWidget] = None):
        super(GenericDialog, self).__init__()
        self.setWindowTitle(title)
        self.setParent(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal if modal else Qt.WindowModality.NonModal)
        self.setLayout(VBoxLayout() if alignment is Alignment.vertical else HBoxLayout())

        if position:
            self.move(position)

    def add_widget(self, widget: QWidget) -> QWidget:
        """
        Add a widget to the layout
        :param widget:
        :return:
        """
        self.layout().addWidget(widget)
        return widget

    def add_label(self, text: str, center_align: bool = True) -> QLabel:
        """
        Add a label to the layout
        :param text:
        :param center_align:
        :return:
        """
        label: QLabel = self.add_widget(QLabel(text))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter if center_align else Qt.AlignmentFlag.AlignLeft)

        return label

    def add_button(self, text: str, tool_tip: str = '', event: Optional[Callable] = None) -> QPushButton:
        """
        Add a button to the layout
        :param text:
        :param tool_tip:
        :param event:
        :return:
        """
        button: QPushButton = self.add_widget(QPushButton(text))
        button.setToolTip(tool_tip)
        button.clicked.connect(event)

        return button


class TestDialog(GenericDialog):
    def __init__(self):
        super(TestDialog, self).__init__(title='Test Dialog', modal=True)
        self.add_label('What is all this about?')
        self.add_button('OK', event=self.close)
        self.resize(180, 80)


if __name__ == '__main__':
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = TestDialog()
    dialog.show()
    sys.exit(app.exec())
