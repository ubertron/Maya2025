from qtpy.QtWidgets import QGroupBox, QWidget, QVBoxLayout


class GroupBox(QGroupBox):
    def __init__(self, widget: QWidget, margin=2, spacing=2):
        super(GroupBox, self).__init__(widget.windowTitle())
        self.widget = widget
        layout = QVBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        self.setLayout(layout)
        layout.addWidget(widget)
