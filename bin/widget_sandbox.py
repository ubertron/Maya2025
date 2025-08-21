from PySide6.QtWidgets import QWidget, QPushButton, QSizePolicy
from random import randint

from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget


class WidgetSandbox(GenericWidget):
    def __init__(self):
        super(WidgetSandbox, self).__init__('Widget Sandbox')
        self.init_button = self.add_button('Init Grid', clicked=self.init_grid)
        self.init_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.grid_widget: GridWidget = self.add_widget(GridWidget())
        self.init_grid()
        self.resize(400, 400)

    def init_grid(self):
        self.grid_widget.clear_layout()
        self.grid_widget.setStyleSheet(f'background-color: rgb({randint(0,128)}, {randint(0,128)}, {randint(0,128)})')
        self.grid_widget.add_label('Tom', 0, 0)
        self.grid_widget.add_label('Dick', 0, 1)
        self.grid_widget.add_label('Harry', 1, 0)
        self.grid_widget.add_label('Sally', 1, 1)
        print(self.grid_widget.row_count)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    widget_sandbox = WidgetSandbox()
    widget_sandbox.show()
    app.exec()
