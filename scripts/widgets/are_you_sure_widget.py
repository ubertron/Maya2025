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
from functools import partial
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QSizePolicy, QWidget
from typing import Optional

from core.core_enums import Alignment
from widgets.generic_widget import GenericWidget


class AreYouSureWidget(GenericWidget):
    responded: Signal = Signal(bool)

    def __init__(self, question: str, modal: bool = True, positive: str = 'Proceed',  negative: str = 'Cancel'):
        super(AreYouSureWidget, self).__init__(title='Are You Sure?')
        self.setWindowModality(Qt.WindowModality.ApplicationModal if modal else Qt.WindowModality.NonModal)
        question_label = self.add_label(question)
        question_label.setMargin(20)
        self.value = True
        button_bar: GenericWidget = self.add_widget(GenericWidget(alignment=Alignment.horizontal))
        button_bar.add_button(text=positive, clicked=partial(self.user_response, True))
        button_bar.add_button(text=negative, clicked=partial(self.user_response, False))
        button_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def user_response(self, arg):
        self.responded.emit(arg)
        self.close()


class DialogTestWidget(GenericWidget):
    def __init__(self):
        super(DialogTestWidget, self).__init__(title='Dialog Test Widget')
        message = 'Proceed to delete stuff?'
        self.dialog = AreYouSureWidget(question=message)
        self.label = self.add_label('Response')
        self.button = self.add_button('Launch', clicked=self.launch_clicked)
        self.dialog.responded.connect(self.user_responded)
        self.setFixedSize(320, 240)

    def launch_clicked(self):
        self.dialog.show()

    def user_responded(self, arg):
        self.label.setText(f'User responded {arg}')


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    app = QApplication()
    widget = DialogTestWidget()
    widget.show()
    app.exec()
