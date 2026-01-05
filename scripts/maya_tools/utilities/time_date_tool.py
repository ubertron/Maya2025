"""Maya Tool that shows the time and date."""
import sys
from datetime import datetime

from core.version_info import VersionInfo, Versions
from widgets.generic_widget import GenericWidget

TOOL_NAME = "Time Date Tool"
VERSIONS = Versions(versions=[
    VersionInfo(name=TOOL_NAME, version="1.0.0", codename="snake", info="first release")
])
UI_SCRIPT = "from maya_tools.utilities import time_date_tool\ntime_date_tool.TimeDateTool().restore()"

class TimeDateTool(GenericWidget):
    def __init__(self):
        super().__init__(title=VERSIONS.title)
        self.label = self.add_label()
        self.add_button(text="Get Time/Date", tool_tip="Get Time/Date", clicked=self.get_time_date_clicked)
        self.setFixedSize(400, 200)

    def get_time_date_clicked(self):
        """Apply the time and date to the label."""
        time_date_string = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.label.setText(time_date_string)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = TimeDateTool()
    widget.show()
    sys.exit(app.exec())
