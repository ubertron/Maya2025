from PySide6.QtWidgets import QGroupBox, QWidget, QVBoxLayout


class GroupBox(QGroupBox):
    def __init__(self, name, widget: QWidget, margin=2, spacing=2):
        super(GroupBox, self).__init__(name)
        self.widget = widget
        layout = QVBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        layout.addWidget(widget)
