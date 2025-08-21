from PySide6.QtWidgets import QApplication, QColorDialog
from PySide6.QtGui import QColor

app = QApplication([])

# Show a color dialog with an initial color (e.g., red)
color = QColorDialog.getColor(QColor("red"), options=QColorDialog.ShowAlphaChannel)

if color.isValid():
    print(f"Selected color: {color.name()}")

app.exec()