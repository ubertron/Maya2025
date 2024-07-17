from functools import partial
from PySide6.QtWidgets import QRadioButton, QButtonGroup, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QGroupBox
from PySide6.QtCore import Signal
from typing import Sequence

from core.core_enums import Alignment


class RadioButtonWidget(QWidget):
    clicked = Signal(int)

    def __init__(self, title: str, button_text_list: Sequence[str], active_id: int = 0,
                 alignment: Alignment = Alignment.horizontal, margin: int = 2, spacing: int = 2):
        super(RadioButtonWidget, self).__init__()
        self.button_text_list = button_text_list
        self.radio_buttons = []
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(margin, margin, margin, margin)
        group_box = QGroupBox(title)
        self.layout().addWidget(group_box)
        layout = QHBoxLayout() if alignment is Alignment.horizontal else QVBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        group_box.setLayout(layout)
        button_group = QButtonGroup(group_box)

        for idx, button in enumerate(button_text_list):
            button = QRadioButton(button)
            layout.addWidget(button)
            button_group.addButton(button)
            button.clicked.connect(partial(self.radioButtonClicked, idx))
            self.radio_buttons.append(button)

        self.radio_buttons[active_id].setChecked(True)

    def radioButtonClicked(self, value):
        self.clicked.emit(value)

    @property
    def active_button_id(self) -> int:
        return next(i for i, value in enumerate(self.radio_buttons) if value.isChecked())

    @property
    def active_text(self) -> int:
        return self.button_text_list[self.active_button_id]


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    radio_button_widget = RadioButtonWidget(title='ABC', button_text_list=['a', 'b', 'c'])
    radio_button_widget.show()
    app.exec()
