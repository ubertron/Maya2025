"""Widget to use for help documentation."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

from core.core_enums import Side
from widgets.generic_widget import GenericWidget


class HelpWidget(GenericWidget):
    """Class for help."""

    def __init__(self, title: str, parent_widget: QWidget) -> None:
        """Init."""
        super().__init__(title=title)
        self.parent_widget = parent_widget

    def add_section(self, title: str, body: str | QWidget) -> QWidget:
        """Add a section with a title and body content in a group box.

        Args:
            title: The section title (displayed as group box title).
            body: Either a string (converted to QLabel) or a QWidget.

        Returns:
            The body widget.
        """
        if isinstance(body, str):
            widget = QLabel(body)
            widget.setWordWrap(True)
        else:
            widget = body

        widget.setWindowTitle(title)
        return self.add_group_box(widget=widget)

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
    widget.add_section(title="Test Section", body="This is the body text for the test section.")
    widget.show()
    app.exec()
