import enum

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from typing import Callable, Optional


class GridWidget(QWidget):
    def __init__(self, title: str = '', margin: int = 4, spacing: int = 2):
        super(GridWidget, self).__init__()
        self.setWindowTitle(title)
        layout: QGridLayout = QGridLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)

    def add_widget(self, widget: QWidget, row: int, column: int, row_span: int = 1, col_span: int = 1) -> QWidget:
        """
        Adds a widget to the layout
        :param widget:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :return:
        """
        self.layout().addWidget(widget, row, column, row_span, col_span)
        return widget

    def add_label(self, *args, row: int, column: int, row_span: int = 1, col_span: int = 1,
                  alignment: enum = Qt.AlignmentFlag.AlignCenter) -> QLabel:
        """
        Adds a label to the layout
        :param args:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param alignment:
        :return:
        """
        label = QLabel(*args)
        label.setAlignment(alignment)

        return self.add_widget(widget=label, row=row, column=column, row_span=row_span, col_span=col_span)

    def add_button(self, label: str, row: int, column: int, row_span: int = 1, col_span: int = 1,
                   tool_tip: Optional[str] = None, event: Optional[Callable] = None):
        """
        Add button to the layout
        :param label:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param tool_tip:
        :param event:
        :return:
        """
        button = QPushButton(label)
        button.setToolTip(tool_tip)

        if event:
            button.clicked.connect(event)

        return self.add_widget(widget=button, row=row, column=column, row_span=row_span, col_span=col_span)


class GridWidgetTest(GridWidget):
    def __init__(self):
        super(GridWidgetTest, self).__init__(title='Test Grid Widget')
        self.label1 = self.add_label('1', row=0, column=0)
        self.label1.setStyleSheet('background-color: green')
        self.label2 = self.add_label('2', row=0, column=1, row_span=2)
        self.label2.setStyleSheet('background-color: red')
        button3: QPushButton = self.add_button('3', row=1, column=0)
        self.add_button('4', row=2, column=0, col_span=2, tool_tip='set the text!', event=self.button4_clicked)
        self.resize(320, 240)
        button3.clicked.connect(self.button3_clicked)

    def button3_clicked(self):
        self.label1.setText('Button 3 clicked')

    def button4_clicked(self):
        self.label2.setText('Button 4 clicked')


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    test_widget = GridWidgetTest()
    test_widget.show()
    app.exec()
