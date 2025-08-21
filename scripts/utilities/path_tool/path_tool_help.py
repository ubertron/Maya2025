from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLabel

from help_widget import HelpWidget


class PathToolHelp(HelpWidget):
    """Class for help."""

    release_notes: str = """Path Tool is a tool to help manage paths.
It allows you to store a set of paths which are saved to a data file.
Path Tool allows you to locate those paths on your machine,
and open them up in contextual applications.

0.1 [genesis] - initial ui and functionality
0.2 [golden scarab] - extension of context menu
0.3 [raindogs]
- delete moved to context menu
- add path now opens a dialog
- copy path to clipboard uses str(path) instead of path.as_posix()
"""
    functionality: str = """- You can add new paths by clicking the 'Add Path' button.
- Then either add the path to the description field, or click the browse button.
- If you use the description field, click 'return' on your keyboard to process the path.
- Functionality on each path is achieved by right-clicking the path item.
- After adding a description, that field can be used as a label to identify the path.
- Paths can be sorted by description or by the full text of the paths themselves.
- The 'Open Data' button' can be used to inspect/edit the saved data file.
"""
    color_key: str = """- Pink: local file (red - local directory)
- Green: workspace file (dark green - workspace directory)
- Blue: depot file (dark blue - depot directory)
- Yellow: script (you can open this directly in VS Code)
- Gray: path not found
"""
    email: str = '<a href="mailto:andrew_davis8@apple.com">Email Tech Art</a>'

    def __init__(self, parent_widget: QWidget) -> None:
        """Init."""
        super().__init__(title="Path Tool Help", parent_widget=parent_widget)
        self.add_text_block(f"Release Notes: {self.parent_widget.tool_title}",
                            self.release_notes)
        self.add_text_block(title="Functionality", text=self.functionality)
        self.add_text_block(title="Color Key", text=self.color_key)
        link_label: QLabel = self.add_text_block("Technical Support", self.email)
        link_label.setOpenExternalLinks(True)
        self.setFixedSize(self.sizeHint())
