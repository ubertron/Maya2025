"""Help widget for Boxy Tool."""
from PySide6.QtWidgets import QWidget

from maya_tools.utilities.boxy.boxy_tool import VERSIONS
from widgets.help_widget import HelpWidget

DESCRIPTION = (
    "Boxy Tool creates parametric bounding box objects that can be used as "
    "placeholders, collision volumes, or reference geometry. Boxy objects maintain "
    "their size attributes and can be easily converted to and from standard poly cubes."
)

FUNCTIONS = (
    "<b>Buttons:</b><br>"
    "&#8226; <b>Generate Boxy:</b> Create a boxy from the current selection (mesh, vertices, "
    "faces, or nothing for a default-sized boxy)<br>"
    "&#8226; <b>Toggle Boxy/Poly-Cube:</b> Convert selected boxy objects to poly cubes, "
    "or poly cubes to boxy objects<br>"
    "&#8226; <b>Concave Boxy from Face:</b> Select a face, find its opposite face searching "
    "inward (concave), and create a boxy spanning both faces<br>"
    "&#8226; <b>Convex Boxy from Face:</b> Select a face, find its opposite face searching "
    "outward (convex), and create a boxy spanning both faces<br>"
    "&#8226; <b>Help:</b> Display this help window<br><br>"
    "<b>Parameters:</b><br>"
    "&#8226; <b>Pivot Position:</b> Set where the pivot point is located (bottom, center, or top)<br>"
    "&#8226; <b>Wireframe Color:</b> Click to choose the wireframe display color<br>"
    "&#8226; <b>Base Name:</b> Name prefix for created boxy objects<br>"
    "&#8226; <b>Default Size:</b> Size used when creating a boxy with nothing selected<br>"
    "&#8226; <b>Inherit Rotation:</b> When checked, boxy inherits the rotation of selected geometry"
)

WIDTH = 480


class BoxyHelp(HelpWidget):
    """Help widget for Boxy Tool."""

    def __init__(self, parent_widget: QWidget):
        """Initialize the help widget."""
        super().__init__(title="Boxy Tool Help", parent_widget=parent_widget)
        self._build_content()
        self.resize(WIDTH, self.sizeHint().height())

    def _build_content(self):
        """Build the help content."""
        self.add_section(title="Description", body=DESCRIPTION)
        self.add_section(title="Functions", body=FUNCTIONS)
        self.add_section(title="Versions", body=self._get_versions_text())

    @staticmethod
    def _get_versions_text() -> str:
        """Generate version history text."""
        lines = []
        for version_info in VERSIONS.versions:
            lines.append(f"&#8226; <b>v{version_info.version}</b> [{version_info.codename}]: {version_info.info}")
        return "<br>".join(lines)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication()
    widget = BoxyHelp(parent_widget=None)
    widget.show()
    app.exec()
