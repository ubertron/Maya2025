from __future__ import annotations

import contextlib
import shiboken6

from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QLayout, QSizePolicy, QSpacerItem
from PySide6.QtCore import Qt

from core.core_enums import Alignment, Side
from core import environment_utils
from typing import Optional, Callable
from core.date_time_utils import get_date_time_string
from icon_button import IconButton
from widgets.layouts import HBoxLayout, VBoxLayout


class GenericWidget(QWidget):
    def __init__(self, title: str = "", alignment: Alignment = Alignment.vertical, margin: int = 2,
                 spacing: int = 2, parent: Optional[QWidget] = None):
        super().__init__()
        self.setWindowTitle(title)
        self.setObjectName(self.__class__.__name__)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setLayout(VBoxLayout() if alignment is Alignment.vertical else HBoxLayout())
        self.set_margin(margin)
        self.set_spacing(spacing)
        self._init_maya_properties()
        self.setWindowTitle(title)

    @property
    def count(self) -> int:
        return len(self.widgets)

    @property
    def widgets(self) -> list[QWidget]:
        layout = self.layout()
        return [layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget() is not None]

    @property
    def workspace_control(self) -> str:
        """Name of the Maya workspace control."""
        return f"{self.windowTitle()}_WorkspaceControl"

    def _init_maya_properties(self):
        """
        Initializes widget properties for Maya
        """
        if environment_utils.is_using_maya_python():
            from maya_tools.maya_environment_utils import MAYA_MAIN_WINDOW
            self.setParent(MAYA_MAIN_WINDOW)
            self.setWindowFlags(Qt.WindowType.Tool if environment_utils.is_using_mac_os() else Qt.WindowType.Window)

    def add_button(self, text: str, tool_tip: str = '', clicked: Optional[Callable] = None) -> QPushButton:
        """
        Add a button to the layout
        :param text:
        :param tool_tip:
        :param clicked:
        :return:
        """
        button: QPushButton = QPushButton(text)
        button.setToolTip(tool_tip)
        if clicked:
            button.clicked.connect(clicked)
        self.add_widget(widget=button)
        return button

    def add_icon_button(self, icon_path: Path, tool_tip: str = "", size: int=32, margin: int = 2,
                        clicked: Callable | None = None) -> IconButton:
        """Add an icon button to the layout."""
        icon_button = IconButton(icon_path=icon_path, tool_tip=tool_tip, size=size, margin=margin, clicked=clicked)
        self.add_widget(widget=icon_button)
        return icon_button

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
        elif side is Side.right:
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return label

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

    def add_stretch(self):
        """
        Add a stretch item to the layout
        """
        self.layout().addStretch(True)

    def add_widget(self, widget: QWidget) -> QWidget | QLabel | QPushButton:
        """
        Add a widget to the layout
        :param widget:
        :return:
        """
        self.layout().addWidget(widget)
        return widget

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

    def replace_layout(self, layout: QLayout):
        """
        Change the layout for a different layout
        :param layout:
        """
        QWidget().setLayout(self.layout())
        self.setLayout(layout)

    def restore(self) -> None:
        """Add the ui to the workspace control."""
        print(f">>> {self.workspace_control}.restore")
        with contextlib.suppress(RuntimeError):
            from maya import OpenMayaUI
        control_ptr = OpenMayaUI.MQtUtil.findControl(self.workspace_control)
        control_widget = shiboken6.wrapInstance(int(control_ptr), QWidget)
        layout = control_widget.layout()
        if layout is not None and not layout.count():
            layout.addWidget(self)

    def show_workspace_control(self, floating: bool = True, retain: bool = True,
                               restore: bool = True, ui_script: str = "") -> str:
        """Build the workspace control."""
        print(f">>> {self.workspace_control}.show_workspace_control | retain={retain} | restore={restore}")
        with contextlib.suppress(RuntimeError):
            from maya import cmds
        if cmds.workspaceControl(self.workspace_control, query=True, exists=True):
            cmds.deleteUI(self.workspace_control)
        control = cmds.workspaceControl(
            self.workspace_control,
            label=self.windowTitle(),
            floating=floating,
            resizeHeight=self.sizeHint().width(),
            resizeWidth=self.sizeHint().height(),
            retain=retain,
            restore=restore,
            uiScript=ui_script,
        )
        self.restore()
        return control


class ExampleGenericWidget(GenericWidget):
    def __init__(self):
        super().__init__(title="Date Time Widget")
        # self.add_stretch()
        self.label = self.add_label("Well what are you waiting for? Click it!")
        # self.add_stretch()
        self.button: QPushButton = self.add_button(text="Click me", tool_tip="Get time", clicked=self.get_time)
        # self.resize(320, 120)

    def get_time(self):
        """
        Event for self.button
        """
        self.label.setText(get_date_time_string())

"""
# Instantiation of dockable widget in Maya
from importlib import reload
from widgets import generic_widget; reload(generic_widget)

ui_script = "from widgets import generic_widget; generic_widget.ExampleGenericWidget().restore()"
widget = generic_widget.ExampleGenericWidget()
widget.show_workspace_control(ui_script=ui_script)
"""


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    tool = ExampleGenericWidget()
    tool.show()
    print(tool.widgets)
    app.exec()
