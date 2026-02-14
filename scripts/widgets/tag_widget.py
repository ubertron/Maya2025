from __future__ import annotations
from enum import Enum
from qtpy.QtWidgets import QLineEdit, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QLayout, QSizePolicy
from qtpy.QtCore import Signal, Qt, QRect, QSize, QPoint


class CaseMode(Enum):
    """Case conversion mode for tags."""
    lower = "lower"
    upper = "upper"
    mixed = "mixed"


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
        # Return minimum size hint - just enough for one row
        if not self._items:
            return QSize(0, 0)
        max_height = 0
        total_width = 0
        spacing = self.spacing()
        for item in self._items:
            hint = item.sizeHint()
            max_height = max(max_height, hint.height())
            total_width += hint.width() + spacing
        margins = self.contentsMargins()
        return QSize(total_width + margins.left() + margins.right(),
                     max_height + margins.top() + margins.bottom())

    def minimumSize(self):
        # Minimum size is just enough for one item
        if not self._items:
            return QSize(0, 0)
        max_height = 0
        max_width = 0
        for item in self._items:
            hint = item.sizeHint()
            max_height = max(max_height, hint.height())
            max_width = max(max_width, hint.width())
        margins = self.contentsMargins()
        return QSize(max_width + margins.left() + margins.right(),
                     max_height + margins.top() + margins.bottom())

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        # Calculate actual height needed for given width
        return self._do_layout(QRect(0, 0, width, 0), test_only=True).height()

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def _do_layout(self, rect, test_only=False):
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(margins.left(), margins.top(),
                                       -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue

            item_width = item.sizeHint().width()
            item_height = item.sizeHint().height()
            next_x = x + item_width + spacing

            # Wrap to next line if needed (but not for the first item on a line)
            if x > effective_rect.x() and next_x - spacing > effective_rect.right():
                x = effective_rect.x()
                y = y + line_height + spacing
                next_x = x + item_width + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item_height)

        total_height = y + line_height - rect.y() + margins.bottom()
        return QSize(rect.width(), max(total_height, 0))


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
                 case_mode: CaseMode = CaseMode.mixed, special_characters: list[str] | None = None,
                 allow_numbers: bool = True, separators: str = "",
                 place_holder_text: str = ""):
        """Initialize TagWidget.

        Args:
            parent: Parent widget
            layout_mode: LayoutMode.flow (wrapping) or LayoutMode.scroll (horizontal scroll)
            case_mode: Case conversion mode - CaseMode.LOWER, CaseMode.UPPER, or CaseMode.MIXED
            special_characters: List of allowed special characters (empty/None = allow all).
                               "_" is always allowed. Example: ["'", " ", "-"]
            allow_numbers: If False, numbers are removed from tags
            separators: String of characters that act as tag separators (e.g., ", " for comma and space).
                       When typing, separators trigger immediate tag creation.
                       When pasting, separators are processed only on return press.
                       Separator characters must not conflict with special_characters restrictions.
            place_holder_text: Placeholder text for the input field
        """
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.layout_mode = layout_mode
        self.case_mode = case_mode
        self.special_characters = special_characters if special_characters is not None else []
        self.allow_numbers = allow_numbers
        self._tags: list[str] = []
        self._previous_text = ""  # Track for paste detection
        self.setLayout(QVBoxLayout())

        # Validate and set separators
        self.separators = self._validate_separators(separators)

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

    def _validate_separators(self, separators: str) -> str:
        """Validate separator characters.

        Separators are used for splitting input, not for tag content,
        so they don't need to be in special_characters.

        Args:
            separators: String of separator characters

        Returns:
            Validated separator string (invalid chars removed)
        """
        if not separators:
            return ""

        valid_separators = []
        for char in separators:
            # Skip duplicates
            if char in valid_separators:
                continue

            # Letters and numbers shouldn't be separators
            if char.isalnum():
                print(f"TagWidget: Separator '{char}' is alphanumeric, skipping")
                continue

            valid_separators.append(char)

        return "".join(valid_separators)

    def _setup_ui(self):
        """Setup UI elements and connections."""
        self.field.returnPressed.connect(self._on_field_return_pressed)
        if self.separators:
            self.field.textChanged.connect(self._on_field_text_changed)
        if self.layout_mode == LayoutMode.scroll:
            # Fixed height for scroll area mode
            self.setFixedHeight(self.sizeHint().height())
        # Flow layout mode allows natural height based on content

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

    def _split_by_separators(self, text: str) -> list[str]:
        """Split text by any separator character.

        Args:
            text: Input text to split

        Returns:
            List of parts (may include empty strings)
        """
        if not self.separators:
            return [text]

        # Replace all separators with a common delimiter, then split
        result = text
        delimiter = self.separators[0]
        for sep in self.separators[1:]:
            result = result.replace(sep, delimiter)
        return result.split(delimiter)

    def _contains_separator(self, text: str) -> bool:
        """Check if text contains any separator character."""
        return any(sep in text for sep in self.separators)

    def _on_field_return_pressed(self):
        """Event for self.field return pressed."""
        text = self.field.text()
        if self.separators and self._contains_separator(text):
            # Split by separators and add each tag
            tags = [t.strip() for t in self._split_by_separators(text) if t.strip()]
            if tags:
                self.add_tags(tags)
                self.field.clear()
        elif self.add_tag(text):
            self.field.clear()
        # Reset previous text tracker
        self._previous_text = ""

    def _on_field_text_changed(self, text: str):
        """Event for self.field text changed (separator mode).

        Distinguishes between typing (process separators immediately) and
        pasting (wait for return to process).
        """
        if not self.separators:
            return

        # Detect if this is a paste (multiple characters added at once)
        len_diff = len(text) - len(self._previous_text)
        is_paste = len_diff > 1

        self._previous_text = text

        # If pasted, don't process separators - wait for return
        if is_paste:
            return

        # Live typing: check if the newly typed character is a separator
        if self._contains_separator(text):
            # Split by separators, add all but the last part as tags
            parts = self._split_by_separators(text)
            tags_to_add = [t.strip() for t in parts[:-1] if t.strip()]
            remainder = parts[-1]  # Keep the part after the last separator in the field

            if tags_to_add:
                self.add_tags(tags_to_add)
                self.field.blockSignals(True)
                self.field.setText(remainder)
                self._previous_text = remainder  # Update tracker
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
                if self.case_mode == CaseMode.lower:
                    result.append(char.lower())
                elif self.case_mode == CaseMode.upper:
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
        """Rebuild all tag pill architools_widgets from the current tags list."""
        # Remove all existing architools_widgets and spacers
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
            # For flow layout, invalidate and activate to recalculate
            self.tag_container.layout().invalidate()
            self.tag_container.layout().activate()
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
                             layout_mode=LayoutMode.flow, case_mode=CaseMode.lower)
    widget_lower.tag_added.connect(lambda tag: print(f"✓ Lower Added: {tag}"))
    widget_lower.add_tag("Python")
    widget_lower.add_tag("Qt")
    widget_lower.add_tag("Widgets")
    container.layout().addWidget(widget_lower)

    # Mode 2: Uppercase with special character restrictions
    widget_upper = TagWidget(label="FlowLayout - Uppercase, apostrophe/dash only:",
                             layout_mode=LayoutMode.flow, case_mode=CaseMode.upper,
                             special_characters=["'", "-"])
    widget_upper.tag_added.connect(lambda tag: print(f"✓ Upper Added: {tag}"))
    widget_upper.add_tag("rock'n'roll")
    widget_upper.add_tag("test@domain.com")  # @ and . will become _
    widget_upper.add_tag("foo-bar")
    container.layout().addWidget(widget_upper)

    # Mode 3: Mixed case, no numbers, space/dash allowed
    widget_mixed = TagWidget(label="ScrollArea - Mixed case, no numbers, space/dash allowed:",
                             layout_mode=LayoutMode.scroll, case_mode=CaseMode.mixed,
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

    # Mode 5: Separator mode (type comma or space to add tags)
    widget_sep = TagWidget(label="Separator mode (try typing 'a, b c' or paste 'x, y, z'):",
                           layout_mode=LayoutMode.flow, separators=", ")
    widget_sep.tag_added.connect(lambda tag: print(f"✓ Separator Added: {tag}"))
    widget_sep.add_tags(["apple", "banana", "cherry"])  # Pre-populated tags
    container.layout().addWidget(widget_sep)

    # Mode 6: Custom separators with restricted special chars
    widget_restricted = TagWidget(label="Semicolon separator, dash/underscore allowed:",
                                  layout_mode=LayoutMode.flow, separators=";",
                                  special_characters=["-", "_", ";"])
    widget_restricted.tag_added.connect(lambda tag: print(f"✓ Restricted Added: {tag}"))
    widget_restricted.add_tags(["foo-bar", "hello_world"])
    container.layout().addWidget(widget_restricted)

    container.layout().addStretch(True)
    container.resize(400, 500)  # Initial size, resizable
    container.show()
    app.exec()


