"""
ROBOTOOLS STUDIO PROPRIETARY SOFTWARE LICENSE

Copyright (c) 2026 Andrew Davis / Robotools Studio. All Rights Reserved.

1. OWNERSHIP
   This software is the proprietary property of Andrew Davis / Robotools Studio.
   All intellectual property rights remain with the copyright holder.

2. RESTRICTIONS
   Without explicit written permission, you may NOT:
   - Copy, reproduce, or distribute this software
   - Modify, adapt, or create derivative works
   - Reverse engineer, decompile, or disassemble this software
   - Remove or alter any proprietary notices
   - Use this software in production environments without pre-arranged
     agreement with Andrew Davis / Robotools Studio
   - Sublicense, rent, lease, or lend this software

3. LICENSING
   Individual and commercial licenses are available.
   For licensing inquiries: andy_j_davis@yahoo.com

4. DISCLAIMER
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
   DAMAGES, OR OTHER LIABILITY ARISING FROM THE USE OF THIS SOFTWARE.

5. PROTECTED TECHNOLOGIES
   - Boxy Plugin and BoxyShape custom node
   - Bounds calculation utilities
   - Related tools and plugins
"""
from __future__ import annotations

from qtpy.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
from qtpy.QtCore import QSettings

from core import DEVELOPER

TOOL_NAME = "BoxyTool"
ADVANCED_PIVOT_KEY = "advanced_pivot_mode"


class BoxySettingsDialog(QDialog):
    """Modal dialog for Boxy tool settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Boxy Settings")
        self.setModal(True)

        self.settings = QSettings(DEVELOPER, TOOL_NAME)

        layout = QVBoxLayout(self)

        # Advanced pivot mode checkbox
        self.advanced_pivot_checkbox = QCheckBox("Advanced Pivot Mode (27 anchors)")
        self.advanced_pivot_checkbox.setToolTip(
            "When enabled, shows all 27 pivot anchors (center, faces, edges, vertices).\n"
            "When disabled, shows only the 7 basic anchors (center and 6 faces)."
        )
        self.advanced_pivot_checkbox.setChecked(self.advanced_pivot_mode)
        layout.addWidget(self.advanced_pivot_checkbox)

        # Button box with OK and Cancel
        button_box = QDialogButtonBox()
        button_box.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setFixedWidth(280)

    @property
    def advanced_pivot_mode(self) -> bool:
        """Get the current advanced pivot mode setting."""
        return self.settings.value(ADVANCED_PIVOT_KEY, False, type=bool)

    def _save_and_accept(self):
        """Save settings and close dialog."""
        self.settings.setValue(ADVANCED_PIVOT_KEY, self.advanced_pivot_checkbox.isChecked())
        self.accept()


def get_advanced_pivot_mode() -> bool:
    """Utility function to get the advanced pivot mode setting without opening dialog."""
    settings = QSettings(DEVELOPER, TOOL_NAME)
    return settings.value(ADVANCED_PIVOT_KEY, False, type=bool)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = BoxySettingsDialog()
    if dialog.exec():
        print(f"Advanced pivot mode: {dialog.advanced_pivot_checkbox.isChecked()}")
    sys.exit(0)
