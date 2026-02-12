from __future__ import annotations
from enum import Enum
from qtpy.QtWidgets import QLineEdit, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QLayout, QSizePolicy
from qtpy.QtCore import Signal, Qt, QRect, QSize, QPoint


class CaseMode(Enum):
    """Case conversion mode for tags."""
    LOWER = "lower"
    UPPER = "upper"
    MIXED = "mixed"


class LayoutMode(Enum):
    """Layout mode for tag display."""
    flow = "flow"
    scroll = "scroll"


class FlowLayout(QLayout):
    """Simple flow layout that wraps items to multiple rows."""

    def __init__(self, margin=2, spacing=2):
        super().__init__()
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def sizeHint(self):
        return self._do_layout(QRect(0, 0, 0, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def _do_layout(self, rect, test_only=False):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue

            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x

            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return QSize(rect.width(), y + line_height - rect.y())


class TagPillWidget(QWidget):
    """Visual tag pill with label and remove button."""
    remove_requested = Signal(str)

    def __init__(self, tag_text: str, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text

        # Layout with label and remove button
        from widgets.layouts import HBoxLayout
        self.setLayout(HBoxLayout(margin=2, spacing=2))

        # Tag text label
        self.label = QLabel(tag_text)
        self.layout().addWidget(self.label)

        # Remove button (X)
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.tag_text))
        self.layout().addWidget(self.remove_btn)

        # Size policy - only take up as much width as needed
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        # Pill styling
        self.setStyleSheet("""
            TagPillWidget {
                background-color: #4a90e2;
                border-radius: 10px;
                padding: 2px 6px;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)


class TagWidget(QWidget):
    """Widget for managing a list of string tags with visual pills."""
    tag_added = Signal(str)      # Emitted when tag added
    tag_removed = Signal(str)    # Emitted when tag removed
    tags_changed = Signal(list)  # Emitted on any change

    def __init__(self, parent: QWidget | None = None, title: str = "", label: str = "", layout_mode: LayoutMode = LayoutMode.flow,
                 case_mode: CaseMode = CaseMode.MIXED, special_characters: list[str] | None = None,
                 allow_numbers: bool = True, comma_separation_mode: bool = False,
                 place_holder_text: str = ""):
        """Initialize TagWidget.

        Args:
            parent: Parent widget
            layout_mode: LayoutMode.flow (wrapping) or LayoutMode.scroll (horizontal scroll)
            case_mode: Case conversion mode - CaseMode.LOWER, CaseMode.UPPER, or CaseMode.MIXED
            special_characters: List of allowed special characters (empty/None = allow all).
                               "_" is always allowed. Example: ["'", " ", "-"]
            allow_numbers: If False, numbers are removed from tags
            comma_separation_mode: If True, commas act as separators (like pressing return)
        """
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.layout_mode = layout_mode
        self.case_mode = case_mode
        self.special_characters = special_characters if special_characters is not None else []
        self.allow_numbers = allow_numbers
        self.comma_separation_mode = comma_separation_mode
        self._tags: list[str] = []
        self.setLayout(QVBoxLayout())

        # Input row: title label + input field (above tags)
        from widgets.layouts import HBoxLayout
        input_row = QWidget()
        input_row.setLayout(HBoxLayout(margin=0, spacing=4))

        self.title_label = QLabel(label)
        if label:
            input_row.layout().addWidget(self.title_label)

        self.field = QLineEdit()
        self.field.setPlaceholderText(place_holder_text)
        input_row.layout().addWidget(self.field)

        self.layout().addWidget(input_row)

        # Create tag container based on layout mode (below input)
        if self.layout_mode == LayoutMode.flow:
            # Flow layout mode - wraps to multiple rows
            self.tag_container = QWidget()
            self.tag_container.setLayout(FlowLayout(margin=2, spacing=4))
            self.layout().addWidget(self.tag_container)
        else:
            # Scroll area mode - single row with horizontal scroll
            self.tag_container = QWidget()
            self.tag_container.setLayout(HBoxLayout(margin=2, spacing=4))

            self.scroll_area = QScrollArea()
            self.scroll_area.setWidget(self.tag_container)
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setFixedHeight(28)  # Single row height for tag pills
            self.layout().addWidget(self.scroll_area)

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI elements and connections."""
        self.field.returnPressed.connect(self._on_field_return_pressed)
        if self.comma_separation_mode:
            self.field.textChanged.connect(self._on_field_text_changed)
        self.resize(320, self.sizeHint().height())
        if self.layout_mode == LayoutMode.flow:
            # Allow dynamic height for flow layout mode
            self.setMinimumHeight(self.sizeHint().height())
        else:
            # Fixed height for scroll area mode
            self.setFixedHeight(self.sizeHint().height())

    def add_tag(self, tag: str) -> bool:
        """Add a tag to the widget.

        Args:
            tag: Tag string to add

        Returns:
            True if tag was added, False if duplicate or invalid
        """
        # Normalize tag according to rules
        tag = self._normalize_tag(tag)

        if not tag:
            return False
        if tag in self._tags:
            return False  # Duplicate

        # Add to list and sort alphabetically (case insensitive)
        self._tags.append(tag)
        self._tags.sort(key=str.lower)

        # Rebuild all tag pills to reflect sorted order
        self._rebuild_tag_pills()

        # Emit signals
        self.tag_added.emit(tag)
        self.tags_changed.emit(self._tags.copy())

        # Update layout geometry to fix FlowLayout visibility
        self._update_layout()

        return True

    def add_tags(self, tags: list[str]) -> list[str]:
        """Add multiple tags to the widget.

        Args:
            tags: List of tag strings to add

        Returns:
            List of tags that were successfully added (after normalization)
        """
        added = []
        for tag in tags:
            if self.add_tag(tag):
                # Get the normalized version that was actually added
                normalized = self._normalize_tag(tag)
                added.append(normalized)
        return added

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the widget.

        Args:
            tag: Tag string to remove

        Returns:
            True if tag was removed, False if not found
        """
        if tag not in self._tags:
            return False

        # Remove from list
        self._tags.remove(tag)

        # Rebuild tag pills
        self._rebuild_tag_pills()

        # Emit signals
        self.tag_removed.emit(tag)
        self.tags_changed.emit(self._tags.copy())

        # Update layout geometry
        self._update_layout()

        return True

    def clear_tags(self):
        """Remove all tags from the widget."""
        # Clear list
        self._tags.clear()

        # Rebuild (removes all pills)
        self._rebuild_tag_pills()

        # Emit signal
        self.tags_changed.emit([])

        # Update layout geometry
        self._update_layout()

    def _on_field_return_pressed(self):
        """Event for self.field return pressed."""
        text = self.field.text()
        if self.comma_separation_mode and "," in text:
            # Split by commas and add each tag
            tags = [t.strip() for t in text.split(",") if t.strip()]
            if self.add_tags(tags):
                self.field.clear()
        elif self.add_tag(text):
            self.field.clear()

    def _on_field_text_changed(self, text: str):
        """Event for self.field text changed (comma separation mode)."""
        if not self.comma_separation_mode:
            return
        if "," in text:
            # Split by comma, add all but the last part as tags
            parts = text.split(",")
            tags_to_add = [t.strip() for t in parts[:-1] if t.strip()]
            remainder = parts[-1]  # Keep the part after the last comma in the field
            if tags_to_add:
                self.add_tags(tags_to_add)
                self.field.blockSignals(True)
                self.field.setText(remainder)
                self.field.blockSignals(False)

    def _on_tag_remove_requested(self, tag: str):
        """Event for tag pill remove button clicked."""
        self.remove_tag(tag)

    def _normalize_tag(self, tag: str) -> str:
        """Normalize tag according to validation rules.

        Args:
            tag: Raw tag string

        Returns:
            Normalized tag string
        """
        # Strip whitespace
        tag = tag.strip()

        if not tag:
            return ""

        # Build normalized string character by character
        result = []
        for char in tag:
            # Check if it's a letter
            if char.isalpha():
                # Apply case mode
                if self.case_mode == CaseMode.LOWER:
                    result.append(char.lower())
                elif self.case_mode == CaseMode.UPPER:
                    result.append(char.upper())
                else:  # CaseMode.MIXED
                    result.append(char)
            # Check if it's a number
            elif char.isdigit():
                if self.allow_numbers:
                    result.append(char)
                # If numbers not allowed, skip the character
            # Check if it's underscore (always allowed)
            elif char == "_":
                result.append(char)
            # Check if it's a special character
            else:
                # If special_characters list is empty, allow all
                if not self.special_characters:
                    result.append(char)
                # Otherwise only allow characters in the list
                elif char in self.special_characters:
                    result.append(char)
                else:
                    # Replace disallowed special character with underscore
                    result.append("_")

        return "".join(result)

    def _rebuild_tag_pills(self):
        """Rebuild all tag pill widgets from the current tags list."""
        # Remove all existing widgets and spacers
        layout = self.tag_container.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if isinstance(widget, TagPillWidget):
                    widget.setParent(None)
                    widget.deleteLater()
                elif widget is None:
                    # It's a spacer/stretch item
                    layout.takeAt(i)

        # Create new pills in sorted order
        for tag in self._tags:
            pill = TagPillWidget(tag)
            pill.remove_requested.connect(self._on_tag_remove_requested)
            layout.addWidget(pill)

        # Add stretch at end for scroll area mode to align pills left
        if self.layout_mode == LayoutMode.scroll:
            layout.addStretch()

    def _update_layout(self):
        """Update layout geometry to ensure proper sizing and visibility."""
        # Update the tag container's geometry
        self.tag_container.updateGeometry()

        # Force layout recalculation
        if self.layout_mode == LayoutMode.flow:
            # For flow layout, update the main widget's size
            self.updateGeometry()
            self.adjustSize()
        else:
            # For scroll area, just update the scroll area
            self.scroll_area.updateGeometry()

    @property
    def tags(self) -> list[str]:
        """Get copy of current tags list."""
        return self._tags.copy()

    @tags.setter
    def tags(self, value: list[str]):
        """Set tags list (clears existing and adds new tags)."""
        self.clear_tags()
        for tag in value:
            self.add_tag(tag)


if __name__ == "__main__":
    # import qdarktheme
    from qtpy.QtWidgets import QApplication
    from widgets.layouts import VBoxLayout

    app = QApplication()
    # app.setStyleSheet(qdarktheme.load_stylesheet())

    # Test container to show both modes
    container = QWidget()
    container.setWindowTitle("TagWidget Container")
    container.setLayout(VBoxLayout())

    # Mode 1: FlowLayout with lowercase only
    widget_lower = TagWidget(label="FlowLayout - Lowercase Only:",
                             layout_mode=LayoutMode.flow, case_mode=CaseMode.LOWER)
    widget_lower.tag_added.connect(lambda tag: print(f"✓ Lower Added: {tag}"))
    widget_lower.add_tag("Python")
    widget_lower.add_tag("Qt")
    widget_lower.add_tag("Widgets")
    container.layout().addWidget(widget_lower)

    # Mode 2: Uppercase with special character restrictions
    widget_upper = TagWidget(label="FlowLayout - Uppercase, apostrophe/dash only:",
                             layout_mode=LayoutMode.flow, case_mode=CaseMode.UPPER,
                             special_characters=["'", "-"])
    widget_upper.tag_added.connect(lambda tag: print(f"✓ Upper Added: {tag}"))
    widget_upper.add_tag("rock'n'roll")
    widget_upper.add_tag("test@domain.com")  # @ and . will become _
    widget_upper.add_tag("foo-bar")
    container.layout().addWidget(widget_upper)

    # Mode 3: Mixed case, no numbers, space/dash allowed
    widget_mixed = TagWidget(label="ScrollArea - Mixed case, no numbers, space/dash allowed:",
                             layout_mode=LayoutMode.scroll, case_mode=CaseMode.MIXED,
                             special_characters=[" ", "-"], allow_numbers=False)
    widget_mixed.tag_added.connect(lambda tag: print(f"✓ Mixed Added: {tag}"))
    widget_mixed.add_tag("Test 123")  # Numbers removed
    widget_mixed.add_tag("Hello World")
    widget_mixed.add_tag("Foo-Bar")
    container.layout().addWidget(widget_mixed)

    # Mode 4: Default (everything allowed)
    widget_default = TagWidget(label="Default - Everything allowed:", layout_mode=LayoutMode.flow)
    widget_default.tag_added.connect(lambda tag: print(f"✓ Default Added: {tag}"))
    widget_default.add_tags(["test@email.com", "123-456", "MixedCase"])
    container.layout().addWidget(widget_default)

    # Mode 5: Comma separation mode (type commas to add tags)
    widget_comma = TagWidget(label="Comma separation mode (try typing 'a, b, c'):",
                             layout_mode=LayoutMode.flow, comma_separation_mode=True)
    widget_comma.tag_added.connect(lambda tag: print(f"✓ Comma Added: {tag}"))
    widget_comma.add_tags(["apple", "banana", "cherry"])  # Pre-populated tags
    container.layout().addWidget(widget_comma)

    container.layout().addStretch(True)
    container.setFixedHeight(container.sizeHint().height())
    container.show()
    app.exec()


