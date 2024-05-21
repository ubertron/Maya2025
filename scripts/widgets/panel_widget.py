from PySide6.QtWidgets import QWidget, QSizePolicy, QLabel
from widgets.layouts import VBoxLayout
from widgets.clickable_label import ClickableLabel
from widgets.generic_widget import GenericWidget


class PanelWidget(QWidget):
    closed_graphic = '►'
    open_graphic = '▼'
    default_inactive_style = 'ClickableLabel {color: rgb(128, 128, 128);}'

    def __init__(self, title: str, widget: QWidget, active: bool = True, styles: tuple = (), hint: bool = False):
        """
        Creates a collapsable panel containing a widget
        :param title: Panel title
        :param widget: Embedded widget
        :param active: Default state
        :param styles: Active/inactive title styles
        :param hint: Calculate panel height from sizeHint()
        """
        super(PanelWidget, self).__init__()
        self.setWindowTitle(title)
        self.default_active_style = self.styleSheet()

        if styles:
            self.active_style, self.inactive_style = styles[0], styles[1]
        else:
            self.active_style = self.default_active_style
            self.inactive_style = self.default_inactive_style

        self.hint: bool = hint
        self.setLayout(VBoxLayout())
        self.panel_header: ClickableLabel = ClickableLabel(title)
        self.widget: QWidget = widget
        self.layout().addWidget(self.panel_header)
        self.layout().addWidget(widget)
        self.layout().addStretch(True)
        self.setup_ui()
        self.active = active
        self.widget.setVisible(self.active)

    def setup_ui(self):
        self.panel_header.clicked.connect(self.toggle_active)
        self.resize(self.sizeHint())

    def toggle_active(self):
        self.active = not self.active
        self.widget.setVisible(self.active)

    @property
    def header_height(self):
        return self.panel_header.sizeHint().height()

    @property
    def widget_height(self):
        return self.widget.sizeHint().height() if self.hint else self.widget.height()

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        self.update_panel_header()
        self.setStyleSheet(self.active_style if value else self.inactive_style)

    def update_panel_header(self):
        self.panel_header.setText(f'{self.state_graphic} {self.windowTitle()}')

    @property
    def state_graphic(self):
        return self.open_graphic if self.active else self.closed_graphic


class PanelWidgetTest(GenericWidget):
    def __init__(self):
        super(PanelWidgetTest, self).__init__(title='Panel Widget Test')
        self.add_widget(PanelWidget('Test Panel Widget', widget=QLabel('Test Label'), active=True))
        self.setFixedSize(400, 80)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication, QLabel
    app = QApplication()
    panel_widget = PanelWidgetTest()
    panel_widget.show()
    app.exec()
