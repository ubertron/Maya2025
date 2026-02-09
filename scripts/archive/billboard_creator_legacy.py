import os
from PIL import Image
from pathlib import Path
from maya import cmds
from maya.OpenMayaUI import MQtUtil
from PySide6.QtWidgets import QDoubleSpinBox, QSizePolicy, QLineEdit, QFileDialog, QWidget
from PySide6.QtGui import QImageReader

from maya_tools.maya_enums import ObjectType
from maya_tools.node_utils import pivot_to_base, move_to_origin
from maya_tools.material_utils import apply_shader, create_lambert_file_texture_shader
from shiboken6 import wrapInstance
from widgets.grid_widget import GridWidget


DALEK_IMAGE: Path = Path(__file__).parents[3].joinpath('images/dalek.png')


class BillboardCreator:
    def __init__(self, image_path: Path, width: float = 1.0):
        assert image_path.exists(), 'Path not found.'
        self.image_path: Path = image_path
        self.billboard_width = width

    def __repr__(self) -> str:
        return f'Path: {self.image_path} [{self.resolution[0]}, {self.resolution[1]}]'

    @property
    def resolution(self) -> tuple[int, int]:
        return Image.open(self.image_path.as_posix()).size

    @property
    def aspect_ratio(self) -> float:
        width, height = self.resolution
        return float(width) / float(height)

    @property
    def billboard_height(self) -> float:
        return self.billboard_width / self.aspect_ratio

    def create(self):
        billboard, shape = cmds.polyPlane(
            name=self.image_path.stem,
            width=self.billboard_width, height=self.billboard_height,
            subdivisionsX=1, subdivisionsY=1,
            createUVs=1,
            axis=(0, 0, 1))
        pivot_to_base(node=billboard)
        move_to_origin(billboard)
        lambert_shader, shading_group = create_lambert_file_texture_shader(texture_path=self.image_path)
        apply_shader(shading_group=shading_group, transforms=billboard)

        for panel in cmds.getPanel(type=ObjectType.modelPanel.name):
            cmds.modelEditor(panel, edit=True, displayTextures=True)

        return billboard, shape


class BillboardCreatorTool(GridWidget):
    def __init__(self):
        super(BillboardCreatorTool, self).__init__('Billboard Creator')
        browse_button = self.add_button('Browse...', row=0, column=0, event=self.browse_button_clicked)
        browse_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.line_edit = self.add_widget(QLineEdit(), row=0, column=1, col_span=2)
        self.add_label('Size:', row=1, column=0)
        self.spin_box: QDoubleSpinBox = self.add_widget(QDoubleSpinBox(), row=1, column=1)
        self.spin_box.setMinimum(0.2)
        self.spin_box.setValue(1)
        self.create_button = self.add_button('Create', row=1, column=2, event=self.create_button_clicked)
        self.resize(600, 48)
        self.refresh()

    def refresh(self):
        self.create_button.setEnabled(self.line_edit.text() != '')

    @property
    def current_path(self):
        return Path(self.line_edit.text())

    @property
    def width(self):
        return self.spin_box.value()

    def browse_button_clicked(self):
        last_dir = self.line_edit.text() if self.current_path else os.getcwd()
        supported_formats = QImageReader.supportedImageFormats()
        image_formats = ' '.join(['*.{}'.format(fo.data().decode()) for fo in supported_formats])
        text_filter = f'Images ({image_formats})'
        file_path, _ = QFileDialog().getOpenFileName(self, 'Open file', dir=last_dir, filter=text_filter)

        if file_path:
            self.line_edit.setText(file_path)
            self.create_button.setEnabled(True)

    def create_button_clicked(self):
        BillboardCreator(image_path=self.current_path, width=self.width).create()


def launch():
    main_window_ptr = MQtUtil.mainWindow()
    maya_main_window = wrapInstance(int(main_window_ptr), QWidget)
    tool = next((x for x in maya_main_window.children() if type(x) is BillboardCreatorTool), None)
    if not tool:
        tool = BillboardCreatorTool()
    tool.show()
