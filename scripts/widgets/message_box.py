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
from typing import Optional

from widgets.generic_dialog import GenericDialog


class MessageBox(GenericDialog):
    def __init__(self, title: str, text: str, fixed_width: Optional[int] = None, parent=None):
        super(MessageBox, self).__init__(title, parent=parent)
        self.add_label(text)
        self.add_button(text='OK', event=self.close)

        if fixed_width:
            self.setFixedSize(fixed_width, self.sizeHint().height())


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication

    app = QApplication()
    dialog = MessageBox(title='Test Message Box', text='Do you understand?', fixed_width=220)
    dialog.show()
    app.exec()
