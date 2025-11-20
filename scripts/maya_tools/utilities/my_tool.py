

from widgets.generic_widget import GenericWidget
from core.date_time_utils import get_date_time_string

UI_SCRIPT = "from maya_tools.utilities import my_tool\nmy_tool.MyTool().restore()"

class MyTool(GenericWidget):
    def __init__(self):
        super().__init__(title="My Tool")
        self.label = self.add_label("label")
        self.button = self.add_button("button", clicked=self.button_clicked)
        self.setMinimumSize(200, 100)

    def button_clicked(self):
        """Event for button clicked."""
        self.label.setText(get_date_time_string())



if __name__ == "__main__":
    import sys
    from PySide6 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    window = MyTool()
    window.show()
    app.exec()
