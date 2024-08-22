from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit


class FloatInputWidget(QLineEdit):
    def __init__(self, minimum=0, maximum=100):
        super(FloatInputWidget, self).__init__()
        validator = QDoubleValidator()
        validator.setRange(minimum, maximum)
        self.setValidator(validator)
