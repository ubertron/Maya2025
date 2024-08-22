from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QPushButton, QLabel, QWidget, QLayout
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
        :param spacing:
        :param parent:
        """
        super(ScrollWidget, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContentsMargins(margin, margin, margin, margin)
        scroll_widget: QScrollArea = QScrollArea()
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFocusPolicy(Qt.NoFocus)
        self.widget: GenericWidget = GenericWidget(title, alignment=alignment)
        scroll_widget.setWidget(self.widget)
        self.layout().addWidget(scroll_widget)

    def add_button(self, text: str, tool_tip: str = '', event: Optional[Callable] = None) -> QPushButton:
        """
        Add a QPushButton to the layout
        :param text: str
        :param tool_tip: str
        :param event: slot method
        :return: QPushbutton
        """
        button: QPushButton = QPushButton(text)
        button.setToolTip(tool_tip)

        if event:
            button.clicked.connect(event)

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

    def add_widget(self, widget: QWidget) -> QWidget:
        """
        Add any QWidget or derivative to the layout
        :param widget: widget
        :return: QWidget
        """
        self.widget.add_widget(widget)
        return widget

    def replace_layout(self, layout: QLayout):
        self.widget.replace_layout(layout)

    def clear_layout(self):
        self.widget.clear_layout()

    def add_stretch(self):
        self.widget.add_stretch()

    def add_spacing(self, value: int):
        self.widget.add_spacing(value)

    @property
    def child_widgets(self) -> list[QWidget]:
        return [self.widget.layout().itemAt(i).widget() for i in range(self.widget.layout().count())]


class TestScrollWidget(ScrollWidget):
    def __init__(self):
        super(TestScrollWidget, self).__init__(title='Test Scroll Widget')
        names = [str(i) for i in range(50)]
        self.add_label(text='\n'.join(names))
        self.add_label(text='Button')


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    test_widget = TestScrollWidget()
    test_widget.show()
    print(test_widget.child_widgets)
    sys.exit(app.exec())
