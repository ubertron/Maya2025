from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QMargins
from __feature__ import true_property, snake_case


class VBoxLayout(QVBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(VBoxLayout, self).__init__()
        self.contents_margins = QMargins(margin, margin, margin, margin)
        self.margin = margin
        self.spacing = spacing


class HBoxLayout(QHBoxLayout):
    def __init__(self, margin: int = 2, spacing: int = 2):
        super(HBoxLayout, self).__init__()
        self.contents_margins = QMargins(margin, margin, margin, margin)
        self.margin = margin
        self.spacing = spacing
