import platform

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QLayout, QSizePolicy, QMainWindow, QSpacerItem
from PySide6.QtCore import Qt
from shiboken6 import wrapInstance
from typing import Optional, Callable

from widgets.layouts import HBoxLayout, VBoxLayout
from core import DARWIN_STR
from core.core_enums import Alignment
from core.environment_utils import is_using_maya_python


class GenericWidget(QWidget):
    def __init__(self, title: str = '', alignment: Alignment = Alignment.vertical, parent: Optional[QWidget] = None, margin: int = 2, spacing: int = 2):
        super(GenericWidget, self).__init__(parent=parent)
        self.title = title
        self.setWindowTitle(self.title)
        self.setObjectName(self.title)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setLayout(VBoxLayout() if alignment is Alignment.vertical else HBoxLayout())
        self.set_margin(margin)
        self.set_spacing(spacing)
        self._init_maya_properties()

    def add_widget(self, widget: QWidget) -> QWidget:
        """
        Add a widget to the layout
        :param widget:
        :return:
        """
        self.layout().addWidget(widget)
        return widget

    def add_label(self, text: str = '', center_align: bool = True) -> QLabel:
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

    def add_spacing(self, value: int):
        """
        Add spacing to the layout
        :param value: size of the spacing
        """
        self.layout().addSpacing(value)

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
        if is_using_maya_python():
            from maya import OpenMayaUI
            self.mayaMainWindow = wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QMainWindow)
            self.setWindowFlags(Qt.Window)
            self.setWindowFlags(Qt.Tool if platform.system() == DARWIN_STR else Qt.Window)


class TestWidget(GenericWidget):
    def __init__(self):
        super(TestWidget, self).__init__(title='Date Time Widget')
        self.add_stretch()
        self.label = self.add_label('Well what are you waiting for? Click it!')
        self.add_stretch()
        self.button: QtWidgets.QPushButton = self.add_button('Click me', tool_tip='Get time', event=self.get_time)
        self.resize(320, 120)

    def get_time(self):
        self.label.setText(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    from datetime import datetime
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    tool = TestWidget()
    tool.show()
    app.exec()
