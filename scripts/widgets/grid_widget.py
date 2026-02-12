"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Custom Qt widget library
   - Related UI components and templates
"""
from __future__ import annotations

# Grid Widget
import contextlib
import enum
import platform

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QSpacerItem, QMainWindow, QComboBox
from qtpy import shiboken
from typing import Callable, Optional

from core import DARWIN_STR
from core.environment_utils import is_using_maya_python
from core.logging_utils import get_logger

LOGGER = get_logger(name=__name__)


class GridWidget(QWidget):
    def __init__(self, title: str = '', margin: int = 4, spacing: int = 2):
        super(GridWidget, self).__init__()
        self.setWindowTitle(title)
        layout: QGridLayout = QGridLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        self._init_maya_properties()

    def _init_maya_properties(self):
        """
        Initializes widget properties for Maya
        """
        if is_using_maya_python():
            from maya import OpenMayaUI
            self.mayaMainWindow = shiboken.wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QMainWindow)
            self.setWindowFlags(Qt.Window)
            self.setWindowFlags(Qt.Tool if platform.system() == DARWIN_STR else Qt.Window)

    @property
    def column_count(self) -> int:
        return self.layout().columnCount()

    @property
    def first_row_empty(self) -> bool:
        """
        The initial grid has one empty row. Check this first so you can populate it.
        :return:
        """
        for i in range(self.column_count):
            item = self.layout().itemAtPosition(0, i)
            if item and item.widget is not None:
                return False
        return True

    @property
    def row_count(self) -> int:
        return self.layout().rowCount()

    @property
    def workspace_control(self) -> str:
        """Name of the Maya workspace control."""
        return f"{self.windowTitle()}_WorkspaceControl"

    def add_button(self, label: str, row: int, column: int, row_span: int = 1, col_span: int = 1,
                   tool_tip: Optional[str] = None, event: Optional[Callable] = None, replace: bool = False):
        """
        Add button to the layout
        :param label:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param tool_tip:
        :param event:
        :param replace: object
        :return:
        """
        button = QPushButton(label)
        button.setToolTip(tool_tip)
        if event:
            button.clicked.connect(event)
        return self.add_widget(
            widget=button, row=row, column=column, row_span=row_span, col_span=col_span, replace=replace)

    def add_combo_box(self, items: list[str], default_index: int, row: int, column: int, row_span: int = 1, col_span: int = 1):
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setCurrentIndex(default_index)
        return self.add_widget(widget=combo_box, row=row, column=column, row_span=row_span, col_span=col_span)

    def add_label(self, text: str, row: int, column: int, row_span: int = 1, col_span: int = 1,
                  alignment: enum = Qt.AlignmentFlag.AlignCenter, replace: bool = False,
                  style: Optional[str] = None, nice: bool = False) -> QLabel:
        """
        Adds a label to the layout
        :param text:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param alignment:
        :param replace:
        :param style:
        :param nice:
        :return:
        """
        label = QLabel(text.replace('_', ' ') if nice else text)
        label.setAlignment(alignment)
        if style:
            label.setStyleSheet(style)
        result = self.add_widget(
            widget=label, row=row, column=column, row_span=row_span, col_span=col_span, replace=replace)
        return result

    def add_widget(self, widget: QWidget, row: int, column: int, row_span: int = 1, col_span: int = 1,
                   replace: bool = False) -> QWidget:
        """
        Adds a widget to the layout
        :param widget:
        :param row:
        :param column:
        :param row_span:
        :param col_span:
        :param replace:
        :return:
        """
        if replace:
            self.delete_widget(row=row, column=column)
        self.layout().addWidget(widget, row, column, row_span, col_span)
        return widget

    def clear_layout(self):
        """
        Remove all architools_widgets and spacer items from the current layout
        """
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if isinstance(item, QSpacerItem):
                self.layout().takeAt(i)
            else:
                item.widget().setParent(None)

    def delete_widget(self, row: int, column: int):
        """
        Removes a widget from a location if it exists
        :param row:
        :param column:
        """
        assert row < self.row_count, 'Invalid row id'
        assert column < self.column_count, 'Invalid column id'
        item = self.layout().itemAtPosition(row, column)
        if item is not None:
            widget = item.widget()
            self.layout().removeWidget(widget)
            widget.deleteLater()

    def delete_row(self, row: int):
        """
        Delete an entire row
        :param row:
        """
        assert row < self.row_count, 'Invalid row id'
        for i in range(self.column_count):
            self.delete_widget(row=row, column=i)

    def get_column_values(self, column: int) -> list:
        values = []
        for i in range(self.row_count):
            item = self.layout().itemAtPosition(i, column)
            values.append(item.widget().text() if item else None)
        return values

    def get_row_by_text(self, text: str, column: int = 0) -> int or None:
        """
        Gets the index of the row whose widget has the value 'text'
        Works for QLabels and QPushButtons
        :param text:
        :param column:
        :return:
        """
        values = self.get_column_values(column=column)
        return values.index(text) if text in values else None

    def restore(self) -> None:
        """Add the ui to the workspace control."""
        with contextlib.suppress(RuntimeError):
            from maya import OpenMayaUI
        control_ptr = OpenMayaUI.MQtUtil.findControl(self.workspace_control)
        control_widget = shiboken.wrapInstance(int(control_ptr), QWidget)
        layout = control_widget.layout()
        if layout is not None and not layout.count():
            layout.addWidget(self)

    def set_text(self, row: int, column: int, text: str, style: Optional[str] = None, nice: bool = False):
        """
        Set the text of an existing widget
        :param row:
        :param column:
        :param text:
        :param style:
        :param nice:
        """
        item = self.layout().itemAtPosition(row, column)
        if item:
            widget: QWidget = item.widget()
            if type(widget) in (QLabel, QPushButton):
                if nice:
                    text = text.replace('_', ' ')
                widget.setText(text)
                if style:
                    widget.setStyleSheet(style)

    def show_workspace_control(
            self, floating: bool = True, retain: bool = True, restore: bool = True, ui_script: str = "") -> str:
        """Build the workspace control."""
        LOGGER.debug(f">>> {self.workspace_control}.show_workspace_control | retain={retain} | restore={restore}")
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


class GridWidgetTest(GridWidget):
    def __init__(self):
        super(GridWidgetTest, self).__init__(title='Test Grid Widget')
        self.init_buttons()

    def init_buttons(self):
        self.label1 = self.add_label('1', row=0, column=0)
        self.label1.setStyleSheet('background-color: green')
        self.label2 = self.add_label('2', row=0, column=1, row_span=2)
        self.label2.setStyleSheet('background-color: red')
        button3: QPushButton = self.add_button('3', row=1, column=0)
        self.add_button('4', row=2, column=0, col_span=2, tool_tip='set the text!', event=self.button4_clicked)
        self.add_label('Remove me', row=3, column=0)
        self.add_label('Remove me', row=3, column=1)
        self.delete_widget(row=3, column=0)
        self.add_label('Replacement', row=3, column=1, replace=True)
        self.resize(320, 240)
        button3.clicked.connect(self.button3_clicked)

    def button3_clicked(self):
        self.label1.setText('Button 3 clicked')

    def button4_clicked(self):
        self.label2.setText('Button 4 clicked')


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    test_widget = GridWidgetTest()
    test_widget.show()
    app.exec()
