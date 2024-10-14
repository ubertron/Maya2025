from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QLayout, QSizePolicy
from PySide6.QtCore import Qt
from core.core_enums import Alignment, Position, WidgetMode, Side
from core.environment_utils import is_using_maya_python, is_using_mac_os
from typing import Optional, Callable
from core.date_time_utils import get_date_time_string
from widgets.layouts import HBoxLayout, VBoxLayout


class GenericWidget(QWidget):
    def __init__(self, title: str = "", alignment: Alignment = Alignment.vertical, margin: int = 2, spacing: int = 2):
        super().__init__()
        self.setWindowTitle(title)
        self.setObjectName(self.__class__.__name__)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setLayout(VBoxLayout() if alignment is Alignment.vertical else HBoxLayout())
        self.set_margin(margin)
        self.set_spacing(spacing)

        if is_using_maya_python():
            self.setParent(self._init_maya_properties())

        self.setWindowTitle(title)

    def add_widget(self, widget: QWidget) -> QWidget:
        """
        Add a widget to the layout
        :param widget:
        :return:
        """
        self.layout().addWidget(widget)
        return widget

    def add_label(self, text: str = '', side: Side = Side.center) -> QLabel:
        """
        Add a label to the layout
        :param text:
        :param side:
        :return:
        """
        label: QLabel = self.add_widget(QLabel(text))

        if side is Side.center:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif side is Position.right:
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)

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

    def replace_layout(self, layout: QLayout):
        """
        Change the layout for a different layout
        :param layout:
        """
        QWidget().setLayout(self.layout())
        self.setLayout(layout)

    def clear_layout(self):
        """
        Remove all widgets and spacer items from the current layout
        """
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)

            if isinstance(item, QSpacerItem):
                self.layout().takeAt(i)
            else:
                item.widget().setParent(None)

    def add_stretch(self):
        """
        Add a stretch item to the layout
        """
        self.layout().addStretch(True)

    def set_margin(self, value: int):
        """
        Set widget margin
        :param value:
        """
        self.layout().setContentsMargins(value, value, value, value)

    def set_spacing(self, value: int):
        """
        Set widget spacing
        :param value:
        """
        self.layout().setSpacing(value)

    def _init_maya_properties(self):
        """
        Initializes widget properties for Maya
        """
        from maya_tools.maya_environment_utils import MAYA_MAIN_WINDOW
        self.mayaMainWindow = MAYA_MAIN_WINDOW
        self.setWindowFlags(Qt.Tool if is_using_mac_os() else Qt.Window)


class ExampleGenericWidget(GenericWidget):
    def __init__(self):
        super(ExampleGenericWidget, self).__init__(title='Date Time Widget')
        self.add_stretch()
        self.label = self.add_label('Well what are you waiting for? Click it!')
        self.add_stretch()
        self.button: QtWidgets.QPushButton = self.add_button('Click me', tool_tip='Get time', event=self.get_time)
        self.resize(320, 120)

    def get_time(self):
        """
        Event for self.button
        """
        self.label.setText(get_date_time_string())


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = ExampleGenericWidget()
    tool.show()
    app.exec()
