"""Help widget for Architools."""
from qtpy.QtWidgets import QWidget

from maya_tools.utilities.architools import TOOL_NAME, VERSIONS
from widgets.help_widget import HelpWidget

DESCRIPTION = (
    "Architools is a procedural architecture toolkit for creating doors, windows, "
    "and staircases from boxy placeholder objects. It integrates with the Boxy system "
    "to provide a streamlined workflow for architectural modeling in Maya."
)

FUNCTIONS = (
    "<b>Toolbar Buttons:</b><br>"
    "&#8226; <b>Create Boxy:</b> Context-sensitive boxy creation - creates default boxy if nothing "
    "selected, rebuilds existing boxy nodes, converts architypes or polycubes to boxy<br>"
    "&#8226; <b>Create Polycube:</b> Context-sensitive polycube creation - creates default polycube if "
    "nothing selected, converts boxy/architypes to polycube, recalculates existing polycubes<br>"
    "&#8226; <b>Concave Boxy from Face:</b> Select a face, find its opposite face searching "
    "inward (concave), and create a boxy spanning both faces<br>"
    "&#8226; <b>Convex Boxy from Face:</b> Select a face, find its opposite face searching "
    "outward (convex), and create a boxy spanning both faces<br>"
    "&#8226; <b>Rotate 90°:</b> Rotates orientation (not regular rotation) by -90° on Y axis. "
    "Works on boxy nodes, polycubes, and architypes - preserves size relative to axes<br>"
    "&#8226; <b>Help:</b> Display this help window<br><br>"
    "<b>General Attributes:</b><br>"
    "&#8226; <b>Default Cube Size:</b> Size used when creating boxy/polycube with nothing selected<br>"
    "&#8226; <b>Skirt Thickness:</b> Thickness of the skirt/baseboard for doors and windows<br>"
    "&#8226; <b>Auto-texture:</b> Automatically apply checker texture to created geometry<br><br>"
    "<b>Door Tab:</b><br>"
    "&#8226; <b>Generate Door:</b> Create door geometry from selected boxy nodes<br>"
    "&#8226; <b>Rotate Door 90°:</b> Rotate selected door or boxy by 90 degrees<br>"
    "&#8226; <b>Frame Size:</b> Width of the door frame<br>"
    "&#8226; <b>Door Depth:</b> Thickness of the door panel<br>"
    "&#8226; <b>Hinge Side:</b> Left or right side for door hinge<br>"
    "&#8226; <b>Opening Side:</b> Front or back direction for door swing<br><br>"
    "<b>Window Tab:</b><br>"
    "&#8226; <b>Generate Window:</b> Create window geometry from selected boxy nodes<br>"
    "&#8226; <b>Rotate Window 90°:</b> Rotate selected window or boxy by 90 degrees<br>"
    "&#8226; <b>Sill Thickness:</b> Height of the window sill<br>"
    "&#8226; <b>Sill Depth:</b> How far the sill protrudes<br>"
    "&#8226; <b>Frame Size:</b> Width of the window frame<br>"
    "&#8226; <b>Skirt Size:</b> Size of the window skirt/trim<br><br>"
    "<b>Staircase Tab:</b><br>"
    "&#8226; <b>Generate Staircase:</b> Create staircase geometry from selected boxy nodes<br>"
    "&#8226; <b>Rotate Staircase 90°:</b> Rotate selected staircase or boxy by 90 degrees<br>"
    "&#8226; <b>Step parameters:</b> Configure step dimensions and staircase properties"
)

WIDTH = 520


class ArchitoolsHelp(HelpWidget):
    """Help widget for Architools."""

    def __init__(self, parent_widget: QWidget):
        """Initialize the help widget."""
        super().__init__(title=f"{TOOL_NAME} Help", parent_widget=parent_widget)
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
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    widget = ArchitoolsHelp(parent_widget=None)
    widget.show()
    app.exec()
