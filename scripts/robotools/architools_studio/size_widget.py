import sys

from qtpy.QtWidgets import QLineEdit, QDoubleSpinBox, QSizePolicy

from core.core_enums import Alignment
from widgets.generic_widget import GenericWidget
from widgets.grid_widget import GridWidget
from widgets.radio_button_widget import RadioButtonWidget


class MinCenterMaxPicker(RadioButtonWidget):
    def __init__(self, title: str):
        super().__init__(
            title=title,
            button_text_list=("Minimum", "Center", "Maximum"),
            active_id=1,
        )


class SizeWidget(GenericWidget):
    default_value: float = 50.0
    def __init__(self):
        super().__init__(title="Size Widget")
        self.add_widget(widget=SizeRowWidget(title="Width"))
        self.add_widget(widget=SizeRowWidget(title="Height"))
        self.add_widget(widget=SizeRowWidget(title="Depth"))

    def _setup_ui(self):
        """asdf"""


class SizeRowWidget(GenericWidget):
    def __init__(self, title: str):
        super().__init__(alignment=Alignment.horizontal)
        self.radio_button_widget: RadioButtonWidget = self.add_widget(widget=RadioButtonWidget(title=title, button_text_list=("Lock", "Constant"), active_id=0))
        self.add_widget(MinCenterMaxPicker(title=f"{title} Lock"))
        self.add_widget(QDoubleSpinBox())
        self._setup_ui()

    def _setup_ui(self):
        self.radio_button_widget.clicked.connect(self.update_ui)
        self.radio_button_widget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred))
        self.update_ui()

    def update_ui(self):
        self.widgets[1].setVisible(self.radio_button_widget.current_button_id == 0)
        self.widgets[2].setVisible(self.radio_button_widget.current_button_id == 1)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = SizeWidget()
    widget.show()
    app.exec()
