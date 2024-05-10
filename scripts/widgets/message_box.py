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
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    dialog = MessageBox(title='Test Message Box', text='Do you understand?', fixed_width=220)
    dialog.show()
    app.exec()
