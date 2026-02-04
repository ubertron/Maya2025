from qtpy.QtCore import Qt
from qtpy.QtWidgets import QScrollArea, QSizePolicy, QPushButton, QLabel, QWidget
from typing import Optional, Callable

from widgets.generic_widget import GenericWidget
from core.core_enums import Alignment


class ScrollWidget(GenericWidget):
    def __init__(self, title: str = '', alignment: Alignment = Alignment.vertical, margin: int = 0,
                 parent: Optional[QWidget] = None):
        """
        Generic widget with internal scroll area
        :param title:
        :param alignment:
        :param margin:
        :param parent:
        """
        super(ScrollWidget, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.widget: GenericWidget = GenericWidget(title, alignment=alignment)
        scroll_widget: QScrollArea = QScrollArea()
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scroll_widget.setWidget(self.widget)
        self.layout().addWidget(scroll_widget)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setContentsMargins(margin, margin, margin, margin)

    def add_button(self, text: str, tool_tip: str = '', clicked: Optional[Callable] = None) -> QPushButton:
        """
        Add a QPushButton to the layout
        :param text: str
        :param tool_tip: str
        :param clicked: slot method
        :return: QPushbutton
        """
        button: QPushButton = QPushButton(text)
        button.setToolTip(tool_tip)

        if clicked:
            button.clicked.connect(clicked)

        return self.widget.add_widget(button)

    def add_label(self, text: str = '', center_align: bool = True) -> QLabel:
        """
        Add a QLabel to the layout
        :param center_align:
        :param text: str
        :return: QLabel
        """
        label = QLabel(text) if text else QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter if center_align else Qt.AlignmentFlag.AlignLeft)
        return self.widget.add_widget(label)

    @property
    def child_widgets(self) -> list[QWidget]:
        return [self.widget.layout().itemAt(i).widget() for i in range(self.widget.layout().count())]


class TestScrollWidget(ScrollWidget):
    def __init__(self):
        super(TestScrollWidget, self).__init__(title='Test Scroll Widget')
        names = [str(i) for i in range(50)]
        my_widget = self.widget.add_widget(GenericWidget())
        my_widget.setMinimumSize(100, 200)
        my_widget.setStyleSheet("color: rgb(255, 255, 255);")
        self.widget.add_label(text='\n'.join(names))
        self.widget.add_label(text='Button')


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    test_widget = TestScrollWidget()
    test_widget.show()
    print(test_widget.child_widgets)
    sys.exit(app.exec())
