""""Widget to use for help documentation."""
from PySide6.QtWidgets import QLabel, QWidget
from core.core_enums import Position, Side
from widgets.generic_widget import GenericWidget


class HelpWidget(GenericWidget):
    """Class for help."""

    def __init__(self, title: str, parent_widget: QWidget) -> None:
        """Init."""
        super().__init__(title=title)
        self.parent_widget = parent_widget

    def add_title(self, text: str) -> QLabel:
        """Add a title label."""
        label: QLabel = self.add_label(text=f"<b>{text}</b>", side=Side.left)
        return label

    def add_text_block(self, title: str, text: str) -> QLabel:
        """Add a text block to the widget."""
        self.add_title(text=title)
        return self.add_label(text=text, side=Side.left)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    widget = HelpWidget(title="Test Help", parent_widget=None)
    widget.add_text_block("asdfasdf", "asldkjflaksdjf;laskdjf;lasdkjf")
    widget.show()
    app.exec()
