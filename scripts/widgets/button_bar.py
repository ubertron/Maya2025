from widgets.generic_widget import GenericWidget
from PySide6.QtWidgets import QSizePolicy

from core.core_enums import Alignment

class ButtonBar(GenericWidget):
    def __init__(self):
        super().__init__(alignment=Alignment.horizontal)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
