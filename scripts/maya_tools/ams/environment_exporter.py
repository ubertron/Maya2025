from PySide6.QtWidgets import QWidget
from typing import Optional

from widgets.generic_widget import GenericWidget


class EnvironmentExporter(GenericWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(EnvironmentExporter, self).__init__('Environment Exporter')
        self.parent_widget: QWidget or None = parent
        self.add_label('Environment Exporter coming soon...')
