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
   - Custom Qt widget library
   - Related UI components and templates
"""
from __future__ import annotations

from qtpy.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QVBoxLayout, QLabel
from qtpy.QtCore import Qt, Signal, QPoint
from qtpy.QtGui import QPainter, QPen, QBrush, QColor, QFont

from robotools.anchor import Anchor, BASIC_ANCHORS


# Three-slice layout: Back, Middle, Front (each is a 3x3 grid)
# Grid positions are (col, row) where (0,0) is top-left
BACK_SLICE = {
    # Row 0 (top)
    (0, 0): Anchor.v2,   # left-top-back
    (1, 0): Anchor.e2,   # top-back
    (2, 0): Anchor.v6,   # right-top-back
    # Row 1 (middle)
    (0, 1): Anchor.e4,   # left-back
    (1, 1): Anchor.f4,   # back (face center)
    (2, 1): Anchor.e6,   # right-back
    # Row 2 (bottom)
    (0, 2): Anchor.v0,   # left-bottom-back
    (1, 2): Anchor.e0,   # bottom-back
    (2, 2): Anchor.v4,   # right-bottom-back
}

MIDDLE_SLICE = {
    # Row 0 (top)
    (0, 0): Anchor.e9,   # left-top
    (1, 0): Anchor.f3,   # top (face center)
    (2, 0): Anchor.e11,  # right-top
    # Row 1 (middle)
    (0, 1): Anchor.f0,   # left (face center)
    (1, 1): Anchor.c,    # center
    (2, 1): Anchor.f1,   # right (face center)
    # Row 2 (bottom)
    (0, 2): Anchor.e8,   # left-bottom
    (1, 2): Anchor.f2,   # bottom (face center)
    (2, 2): Anchor.e10,  # right-bottom
}

FRONT_SLICE = {
    # Row 0 (top)
    (0, 0): Anchor.v3,   # left-top-front
    (1, 0): Anchor.e3,   # top-front
    (2, 0): Anchor.v7,   # right-top-front
    # Row 1 (middle)
    (0, 1): Anchor.e5,   # left-front
    (1, 1): Anchor.f5,   # front (face center)
    (2, 1): Anchor.e7,   # right-front
    # Row 2 (bottom)
    (0, 2): Anchor.v1,   # left-bottom-front
    (1, 2): Anchor.e1,   # bottom-front
    (2, 2): Anchor.v5,   # right-bottom-front
}

# Basic mode only shows middle slice face centers + center
BASIC_POSITIONS = {Anchor.c, Anchor.f0, Anchor.f1, Anchor.f2, Anchor.f3, Anchor.f4, Anchor.f5}

# Human-readable names for tooltips
ANCHOR_NAMES = {
    # Center
    Anchor.c: "Center",
    # Face centers
    Anchor.f0: "Left face",
    Anchor.f1: "Right face",
    Anchor.f2: "Bottom face",
    Anchor.f3: "Top face",
    Anchor.f4: "Back face",
    Anchor.f5: "Front face",
    # Edge midpoints
    Anchor.e0: "Bottom-back edge",
    Anchor.e1: "Bottom-front edge",
    Anchor.e2: "Top-back edge",
    Anchor.e3: "Top-front edge",
    Anchor.e4: "Left-back edge",
    Anchor.e5: "Left-front edge",
    Anchor.e6: "Right-back edge",
    Anchor.e7: "Right-front edge",
    Anchor.e8: "Left-bottom edge",
    Anchor.e9: "Left-top edge",
    Anchor.e10: "Right-bottom edge",
    Anchor.e11: "Right-top edge",
    # Vertices
    Anchor.v0: "Left-bottom-back vertex",
    Anchor.v1: "Left-bottom-front vertex",
    Anchor.v2: "Left-top-back vertex",
    Anchor.v3: "Left-top-front vertex",
    Anchor.v4: "Right-bottom-back vertex",
    Anchor.v5: "Right-bottom-front vertex",
    Anchor.v6: "Right-top-back vertex",
    Anchor.v7: "Right-top-front vertex",
}


class SliceWidget(QWidget):
    """A single 3x3 slice of the cube."""

    anchor_clicked = Signal(Anchor)

    COLOR_BACKGROUND = QColor(45, 45, 45)
    COLOR_GRID = QColor(70, 70, 70)
    COLOR_CENTER = QColor(255, 255, 255)
    COLOR_FACE = QColor(100, 180, 100)
    COLOR_EDGE = QColor(100, 130, 200)
    COLOR_VERTEX = QColor(200, 100, 100)
    COLOR_SELECTED = QColor(255, 200, 50)
    COLOR_HOVER = QColor(180, 180, 180)
    COLOR_DISABLED = QColor(60, 60, 60)

    def __init__(self, slice_data: dict, label: str, parent=None):
        super().__init__(parent)
        self._slice_data = slice_data
        self._label = label
        self._selected_anchor: Anchor | None = None
        self._hovered_anchor: Anchor | None = None
        self._advanced_mode = False

        self.setMinimumSize(70, 70)
        self.setMouseTracking(True)

    @property
    def advanced_mode(self) -> bool:
        return self._advanced_mode

    @advanced_mode.setter
    def advanced_mode(self, value: bool):
        self._advanced_mode = value
        self.update()

    @property
    def selected_anchor(self) -> Anchor | None:
        return self._selected_anchor

    @selected_anchor.setter
    def selected_anchor(self, anchor: Anchor | None):
        self._selected_anchor = anchor
        self.update()

    def _is_anchor_visible(self, anchor: Anchor) -> bool:
        """Check if anchor should be visible based on mode."""
        if self._advanced_mode:
            return True
        return anchor in BASIC_POSITIONS

    def _grid_to_pixel(self, col: int, row: int) -> tuple[int, int]:
        """Convert grid position to pixel coordinates."""
        margin = 8
        w = self.width() - 2 * margin
        h = self.height() - 2 * margin - 12  # Reserve space for label
        cell_w = w / 2
        cell_h = h / 2
        px = margin + col * cell_w
        py = margin + 12 + row * cell_h  # Offset for label
        return int(px), int(py)

    def _get_anchor_at_pos(self, pos: QPoint) -> Anchor | None:
        """Get anchor at pixel position."""
        hit_radius = 10
        for (col, row), anchor in self._slice_data.items():
            if not self._is_anchor_visible(anchor):
                continue
            px, py = self._grid_to_pixel(col, row)
            dx = pos.x() - px
            dy = pos.y() - py
            if dx * dx + dy * dy <= hit_radius * hit_radius:
                return anchor
        return None

    def _get_anchor_color(self, anchor: Anchor) -> QColor:
        """Get the color for an anchor based on its type."""
        if anchor == Anchor.c:
            return self.COLOR_CENTER
        elif anchor.name.startswith('f'):
            return self.COLOR_FACE
        elif anchor.name.startswith('e'):
            return self.COLOR_EDGE
        else:
            return self.COLOR_VERTEX

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.COLOR_BACKGROUND)

        # Draw label
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.drawText(4, 10, self._label)

        # Draw grid lines
        pen = QPen(self.COLOR_GRID)
        pen.setWidth(1)
        painter.setPen(pen)

        margin = 8
        top_offset = 12
        w = self.width() - 2 * margin
        h = self.height() - 2 * margin - top_offset

        # Vertical lines
        for i in range(3):
            x = margin + i * (w / 2)
            painter.drawLine(int(x), margin + top_offset, int(x), self.height() - margin)
        # Horizontal lines
        for i in range(3):
            y = margin + top_offset + i * (h / 2)
            painter.drawLine(margin, int(y), self.width() - margin, int(y))

        # Draw anchor points
        for (col, row), anchor in self._slice_data.items():
            px, py = self._grid_to_pixel(col, row)

            visible = self._is_anchor_visible(anchor)
            is_selected = anchor == self._selected_anchor
            is_hovered = anchor == self._hovered_anchor

            if not visible:
                # Draw dimmed dot for non-visible anchors
                painter.setPen(QPen(self.COLOR_DISABLED, 1))
                painter.setBrush(QBrush(self.COLOR_DISABLED))
                painter.drawEllipse(QPoint(px, py), 3, 3)
                continue

            # Determine size and color
            radius = 7 if is_selected else (6 if is_hovered else 5)

            if is_selected:
                color = self.COLOR_SELECTED
            elif is_hovered:
                color = self.COLOR_HOVER
            else:
                color = self._get_anchor_color(anchor)

            # Draw circle
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPoint(px, py), radius, radius)

        painter.end()

    def mouseMoveEvent(self, event):
        anchor = self._get_anchor_at_pos(event.position().toPoint())
        if anchor != self._hovered_anchor:
            self._hovered_anchor = anchor
            self.setCursor(Qt.CursorShape.PointingHandCursor if anchor else Qt.CursorShape.ArrowCursor)
            # Set tooltip with descriptive name
            if anchor:
                self.setToolTip(ANCHOR_NAMES.get(anchor, anchor.name))
            else:
                self.setToolTip("")
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            anchor = self._get_anchor_at_pos(event.position().toPoint())
            if anchor:
                self.anchor_clicked.emit(anchor)

    def leaveEvent(self, event):
        if self._hovered_anchor:
            self._hovered_anchor = None
            self.update()


class AnchorPicker(QWidget):
    """Visual picker widget for selecting anchor points on a cube.

    Shows three slices of the cube: Back, Middle, Front.
    Each slice is a 3x3 grid showing the anchor points at that Z-depth.
    """

    anchor_selected = Signal(Anchor)

    def __init__(self, parent=None, advanced_mode: bool = False, default: Anchor = Anchor.c):
        super().__init__(parent)
        self._advanced_mode = advanced_mode
        self._selected_anchor: Anchor = default

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Create three slice widgets
        self._back_slice = SliceWidget(BACK_SLICE, "Back", self)
        self._middle_slice = SliceWidget(MIDDLE_SLICE, "Middle", self)
        self._front_slice = SliceWidget(FRONT_SLICE, "Front", self)

        layout.addWidget(self._back_slice)
        layout.addWidget(self._middle_slice)
        layout.addWidget(self._front_slice)

        # Connect signals
        self._back_slice.anchor_clicked.connect(self._on_anchor_clicked)
        self._middle_slice.anchor_clicked.connect(self._on_anchor_clicked)
        self._front_slice.anchor_clicked.connect(self._on_anchor_clicked)

        # Apply initial state
        self._update_slices()

        self.setMinimumSize(220, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    @property
    def advanced_mode(self) -> bool:
        return self._advanced_mode

    @advanced_mode.setter
    def advanced_mode(self, value: bool):
        if self._advanced_mode != value:
            self._advanced_mode = value
            if not value and self._selected_anchor not in BASIC_ANCHORS:
                self._selected_anchor = Anchor.c
                self.anchor_selected.emit(self._selected_anchor)
            self._update_slices()

    @property
    def selected_anchor(self) -> Anchor:
        return self._selected_anchor

    @selected_anchor.setter
    def selected_anchor(self, anchor: Anchor):
        if anchor != self._selected_anchor:
            if not self._advanced_mode and anchor not in BASIC_ANCHORS:
                return
            self._selected_anchor = anchor
            self._update_slices()

    def _update_slices(self):
        """Update all slices with current state."""
        for slice_widget in (self._back_slice, self._middle_slice, self._front_slice):
            slice_widget.advanced_mode = self._advanced_mode
            slice_widget.selected_anchor = self._selected_anchor

    def _on_anchor_clicked(self, anchor: Anchor):
        """Handle anchor click from any slice."""
        if anchor != self._selected_anchor:
            self._selected_anchor = anchor
            self._update_slices()
            self.anchor_selected.emit(anchor)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QVBoxLayout, QCheckBox

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Anchor Picker Test")
    layout = QVBoxLayout(window)

    picker = AnchorPicker(advanced_mode=False)
    layout.addWidget(picker)

    checkbox = QCheckBox("Advanced Mode (27 anchors)")
    checkbox.stateChanged.connect(lambda state: setattr(picker, 'advanced_mode', bool(state)))
    layout.addWidget(checkbox)

    label = QLabel("Selected: Center")
    layout.addWidget(label)

    def on_anchor_selected(anchor: Anchor):
        label.setText(f"Selected: {ANCHOR_NAMES.get(anchor, anchor.name)}")

    picker.anchor_selected.connect(on_anchor_selected)

    window.resize(300, 150)
    window.show()
    sys.exit(app.exec())
